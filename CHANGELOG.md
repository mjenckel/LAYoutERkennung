Change Log
==========
Versioned according to [Semantic Versioning](http://semver.org/).

## Unreleased

## [1.6.0] - 2021-05-20

Removed:

  * `ocrd-anybaseocr-block-segmenation` was broken and caused spurious CI errors

## [1.5.0] - 2021-05-19

Changed:

  * Rewritten `ocrd-anybaseocr-block-segmentation` and `ocrd-anybaseocr-tiseg`, #79

## [1.4.1] - 2021-04-23

Fixed:

  * Re-introduce requirement on `ocrd-fork-ocropy`

## [1.4.0] - 2021-04-23

Changed:

  * Cropping rewritten, ht @bertsky, [improvements visualized](https://bertsky.github.io/ocrd_anybaseocr), #84

## [1.3.0] - 2021-01-28

Changed:

  * Use the OCR-D/core `resmgr` mechanism to resolve file parameters

## [1.2.0] - 2021-01-27

Please disregard, forgot to merge #78

## [1.1.0] - 2020-11-16

Fixed:

  * crop: remove `operation_level` parameter
  * crop: remove `force` parameter
  * crop: fix setting pageId of derived images

## [1.0.2] - 2020-09-24

Fixed:

  * logging according to https://github.com/OCR-D/core/pull/599

## [1.0.1] - 2020-08-24

Fixed:

  * replace copy&pasted metadata addition with `self.add_metadata`, #67

## [1.0.0] - 2020-08-21

Fixed:

  * all processors runnable (though dewarping only with CUDA)
  * fix pix2pixhd installation, #64
  * adapt to 1-output-file-group convention, #66

## [0.0.5] - 2020-08-04

Fixed:

  * Refactoring to make tools installable, with `--help` and `-J` working

## [0.0.4] - 2020-07-08

Fixed:

  * keras should be `>= 2.3.0, < 2.4.0`, #63

## [0.0.3] - 2020-05-14

Fixed:

  * Graceful degradation to CPU processing if CUDA not available - AGAIN, ht @bertsky, #58

## [0.0.2] - 2020-05-06

Fixed:

  * Graceful degradation to CPU processing if CUDA not available, #56

<!-- link-labels -->
[1.6.0]: ../../compare/v1.6.0...v1.5.0
[1.5.0]: ../../compare/v1.5.0...v1.4.1
[1.4.1]: ../../compare/v1.4.1...v1.4.0
[1.4.0]: ../../compare/v1.4.0...v1.3.0
[1.3.0]: ../../compare/v1.1.0...v1.2.0
[1.2.0]: ../../compare/v1.2.0...v1.1.0
[1.1.0]: ../../compare/v1.1.0...v1.0.2
[1.0.2]: ../../compare/v1.0.2...v1.0.1
[1.0.1]: ../../compare/v1.0.1...v1.0.0
[1.0.0]: ../../compare/v1.0.0...v0.0.5
[0.0.5]: ../../compare/v0.0.5...v0.0.4
[0.0.4]: ../../compare/v0.0.3...v0.0.4
[0.0.3]: ../../compare/v0.0.2...v0.0.3
[0.0.2]: ../../compare/HEAD...v0.0.2
