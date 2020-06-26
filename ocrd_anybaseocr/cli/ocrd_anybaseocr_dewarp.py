# pylint: disable=wrong-import-order, import-error, too-few-public-methods
# pylint: disable=too-many-locals, line-too-long, invalid-name, too-many-arguments
# pylint: disable=missing-docstring

import sys
import os

from ..constants import OCRD_TOOL

from ocrd import Processor
from ocrd_models.ocrd_page import (
    to_xml,
    AlternativeImageType,
    MetadataItemType,
    LabelsType, LabelType)

from ocrd_utils import getLogger, concat_padded, MIMETYPE_PAGE
from ocrd_modelfactory import page_from_file
from pylab import array
from pathlib import Path

import torch
import ocrolib

from ..pix2pixhd.options.test_options import TestOptions
from ..pix2pixhd.models.models import create_model
from ..pix2pixhd.data.data_loader import CreateDataLoader

TOOL = 'ocrd-anybaseocr-dewarp'
LOG = getLogger('OcrdAnybaseocrDewarper')
FALLBACK_IMAGE_GRP = 'OCR-D-IMG-DEWARP'

def prepare_data(opt, page_img):

    data_loader = CreateDataLoader(opt)
    data_loader.dataset.A_paths = [page_img.filename]
    data_loader.dataset.dataset_size = len(data_loader.dataset.A_paths)
    data_loader.dataloader = torch.utils.data.DataLoader(data_loader.dataset,
                                                         batch_size=opt.batchSize,
                                                         shuffle=not opt.serial_batches,
                                                         num_workers=int(opt.nThreads))
    dataset = data_loader.load_data()
    return dataset

def prepare_options(gpu_id, dataroot, model_path, resize_or_crop, loadSize, fineSize):
    # TODO oh boy
    sys.argv = [sys.argv[0]]
    # pix2pixHD BaseOptions.parse already uses gpu_ids
    sys.argv.extend(['--gpu_ids', str(gpu_id)])
    opt = TestOptions().parse(save=False)
    opt.nThreads = 1   # test code only supports nThreads = 1
    opt.batchSize = 1  # test code only supports batchSize = 1
    opt.serial_batches = True  # no shuffle
    opt.no_flip = True  # no flip
    opt.checkpoints_dir = model_path.parents[0]
    opt.dataroot = dataroot
    opt.name = model_path.name
    opt.label_nc = 0
    opt.no_instance = True
    opt.resize_or_crop = resize_or_crop
    opt.n_blocks_global = 10
    opt.n_local_enhancers = 2
    opt.loadSize = loadSize
    opt.fineSize = fineSize

    model = create_model(opt)

    return opt, model

class OcrdAnybaseocrDewarper(Processor):

    def __init__(self, *args, **kwargs):
        kwargs['ocrd_tool'] = OCRD_TOOL['tools'][TOOL]
        kwargs['version'] = OCRD_TOOL['version']
        super(OcrdAnybaseocrDewarper, self).__init__(*args, **kwargs)


    def process(self):
        try:
            page_grp, self.image_grp = self.output_file_grp.split(',')
        except ValueError:
            page_grp = self.output_file_grp
            self.image_grp = FALLBACK_IMAGE_GRP
            LOG.info(
                "No output file group for images specified, falling back to '%s'", FALLBACK_IMAGE_GRP)
        if not torch.cuda.is_available():
            LOG.warning("torch cannot detect CUDA installation.")
            self.parameter['gpu_id'] = -1

        model_path = Path(self.parameter['model_path'])
        if not model_path.is_file():
            LOG.error("""\
                    pix2pixHD model file was not found at '%s'. Make sure the this file exists.
                """ % model_path)
            sys.exit(1)

        opt, model = prepare_options(
            gpu_id=self.parameter['gpu_id'],
            dataroot=self.input_file_grp,
            model_path=model_path,
            resize_or_crop=self.parameter['imgresize'],
            loadSize=self.parameter['resizeHeight'],
            fineSize=self.parameter['resizeWidth'],
        )

        oplevel = self.parameter['operation_level']
        for (n, input_file) in enumerate(self.input_files):
            page_id = input_file.pageId or input_file.ID
            LOG.info("INPUT FILE %s", page_id)

            pcgts = page_from_file(self.workspace.download_file(input_file))
            metadata = pcgts.get_Metadata()
            metadata.add_MetadataItem(
                MetadataItemType(type_="processingStep",
                                 name=self.ocrd_tool['steps'][0],
                                 value=TOOL,
                                 Labels=[LabelsType(  # externalRef="parameters",
                                     Label=[LabelType(type_=name,
                                                      value=self.parameter[name])
                                            for name in self.parameter.keys()])]))

            page = pcgts.get_Page()

            page_image, page_xywh, _ = self.workspace.image_from_page(
                page, page_id, feature_filter='dewarped', feature_selector='binarized')  # images should be deskewed and cropped
            if oplevel == 'page':
                dataset = self.prepare_data(opt, page_image)
                orig_img_size = page_image.size
                self._process_segment(
                    model, dataset, page, page_xywh, page_id, input_file, orig_img_size, n)
            else:
                regions = page.get_TextRegion() + page.get_TableRegion()  # get all regions?
                if not regions:
                    LOG.warning("Page '%s' contains no text regions", page_id)
                for _, region in enumerate(regions):
                    region_image, region_xywh = self.workspace.image_from_segment(
                        region, page_image, page_xywh)
                    # TODO: not tested on regions
                    # TODO: region has to exist as a physical file to be processed by pix2pixHD
                    dataset = self.prepare_data(opt, region_image)
                    orig_img_size = region_image.size
                    self._process_segment(
                        model, dataset, page, region_xywh, region.id, input_file, orig_img_size, n)

            # Use input_file's basename for the new file -
            # this way the files retain the same basenames:
            file_id = input_file.ID.replace(self.input_file_grp, page_grp)
            if file_id == input_file.ID:
                file_id = concat_padded(page_grp, n)
            self.workspace.add_file(
                ID=file_id,
                file_grp=page_grp,
                pageId=input_file.pageId,
                mimetype=MIMETYPE_PAGE,
                local_filename=os.path.join(page_grp,
                                            file_id + '.xml'),
                content=to_xml(pcgts).encode('utf-8'),
                force=self.parameter['force']
            )

    def _process_segment(self, model, dataset, page, page_xywh, page_id, input_file, orig_img_size, n):
        for _, data in enumerate(dataset):
            w, h = orig_img_size
            generated = model.inference(
                data['label'], data['inst'], data['image'])
            dewarped = array(generated.data[0].permute(1, 2, 0).detach().cpu())
            bin_array = array(255*(dewarped > ocrolib.midrange(dewarped)), 'B')
            dewarped = ocrolib.array2pil(bin_array)
            dewarped = dewarped.resize((w, h))

            page_xywh['features'] += ',dewarped'

            file_id = input_file.ID.replace(
                self.input_file_grp, self.image_grp)
            if file_id == input_file.ID:
                file_id = concat_padded(self.image_grp, n)

            file_path = self.workspace.save_image_file(dewarped,
                                                       file_id,
                                                       page_id=page_id,
                                                       file_grp=self.image_grp,
                                                       force=self.parameter['force']
                                                      )
            page.add_AlternativeImage(AlternativeImageType(
                filename=file_path, comments=page_xywh['features']))
