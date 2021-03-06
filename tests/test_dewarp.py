# pylint: disable=import-error, unused-import, missing-docstring
from pathlib import Path

from ocrd import Resolver, Workspace
from ocrd.processor.base import run_processor
from ocrd_utils import MIMETYPE_PAGE
import torch
import pytest

from ocrd_anybaseocr.cli.ocrd_anybaseocr_dewarp import OcrdAnybaseocrDewarper # FIXME srsly y

from tests.base import TestCase, assets, main, copy_of_directory

class AnyocrDewarperTest(TestCase):

    def setUp(self):
        self.model_path = Path(Path.cwd(), 'models/latest_net_G.pth')
        self.resolver = Resolver()

    def test_crop(self):
        if not torch.cuda.is_available():
            pytest.skip('CUDA is not available, cannot test dewarping')
        with copy_of_directory(assets.path_to('dfki-testdata/data')) as wsdir:
            ws = Workspace(self.resolver, wsdir)
            pagexml_before = len(ws.mets.find_files(mimetype=MIMETYPE_PAGE))
            run_processor(
                OcrdAnybaseocrDewarper,
                resolver=self.resolver,
                mets_url=str(Path(wsdir, 'mets.xml')),
                input_file_grp='BIN',
                output_file_grp='DEWARP-TEST',
                parameter={'model_path': str(self.model_path)}
            )
            ws.reload_mets()
            pagexml_after = len(ws.mets.find_files(mimetype=MIMETYPE_PAGE))
            self.assertEqual(pagexml_after, pagexml_before + 1)

if __name__ == "__main__":
    main(__file__)

