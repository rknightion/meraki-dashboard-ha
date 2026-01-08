---
layout: default
title: Changelog
description: Release history and changelog for the Meraki Dashboard Home Assistant Integration
---

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.36.0](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.35.0...v0.36.0) (2026-01-08)


### Features

* add camera platform support ([31920a6](https://github.com/rknightion/meraki-dashboard-ha/commit/31920a6df0793fe473ca8a9e25a00714f2bd5961))
* add MV camera data transformer ([0580a0c](https://github.com/rknightion/meraki-dashboard-ha/commit/0580a0cec87bb6781ef44705538793ba4d98dbb6))
* add MV camera hub data handling ([ec5ea47](https://github.com/rknightion/meraki-dashboard-ha/commit/ec5ea478644abdfc1c67e912dbd204d55f38a031))
* add MV camera support to const and types ([84dede4](https://github.com/rknightion/meraki-dashboard-ha/commit/84dede43018511c4b67a537ce016e11af8e34d11))
* add MV capability detection ([0cb8222](https://github.com/rknightion/meraki-dashboard-ha/commit/0cb8222579f12598d27f2c266ebde12dfc67ffda))
* add MV coordinator and sensor setup ([e402a58](https://github.com/rknightion/meraki-dashboard-ha/commit/e402a588b711ac58a0b14d377ef612a6c92a41e6))
* add MV device sensor entities ([a6316f8](https://github.com/rknightion/meraki-dashboard-ha/commit/a6316f85a4fc7528d2551a63e9f73d0070b3ea85))
* add MV entity factory registrations ([d590e93](https://github.com/rknightion/meraki-dashboard-ha/commit/d590e932aa321294eacf4fdd9476ce73b56c16e7))
* add MV support to config and discovery ([90d3e6e](https://github.com/rknightion/meraki-dashboard-ha/commit/90d3e6ecebb0a59a5c5a7b23d844d82d9b0c12cd))
* add MV support to platform registration ([55f6cdb](https://github.com/rknightion/meraki-dashboard-ha/commit/55f6cdb461c380610a811e1a2793ced6ce8f1601))
* add MV switch entity for RTSP control ([353b44b](https://github.com/rknightion/meraki-dashboard-ha/commit/353b44b5d4944a9e91a37742df7cbbc0394c81a4))
* add set_camera_rtsp service ([c6fba9f](https://github.com/rknightion/meraki-dashboard-ha/commit/c6fba9fa0da35021ac3d63652db455519688bdd4))
* **config:** use async Meraki client and robust error handling ([149390d](https://github.com/rknightion/meraki-dashboard-ha/commit/149390d4d6a8ea7ba1d2ae12b6e9cac3f1246d84))
* **const:** define new MV/org metrics and rate limits ([d24a2ba](https://github.com/rknightion/meraki-dashboard-ha/commit/d24a2ba52b602dad7164f5cd7e83112ae2d36375))
* **devices:** add MV sensor descriptions and org rate sensors ([ac7fd3c](https://github.com/rknightion/meraki-dashboard-ha/commit/ac7fd3c2d64493f439b059538d2021c2bd7110db))
* **mv:** add MV binary sensors and camera init docstrings ([4250a84](https://github.com/rknightion/meraki-dashboard-ha/commit/4250a842ac585b53c633c77a7af05a8e49ce0727))
* **rate:** add async Meraki rate limiter utility ([2be2ae0](https://github.com/rknightion/meraki-dashboard-ha/commit/2be2ae01a0febd7a11f478649e8fc0b68fb507fc))
* **transform:** extend MV transformers and org metrics ([a6231fe](https://github.com/rknightion/meraki-dashboard-ha/commit/a6231fe8c11c849c5b71b35fa416fbd56857d637))


### Performance Improvements

* **coordinator:** entity cleanup and event timeouts ([ec3e626](https://github.com/rknightion/meraki-dashboard-ha/commit/ec3e626c488d067d71c2db8af10031969ce1c916))


### Documentation

* add camera service documentation ([136c3b2](https://github.com/rknightion/meraki-dashboard-ha/commit/136c3b2328cdfc7abcb0a0ddd575d4eb140788a4))
* update supported entities documentation ([3e33b14](https://github.com/rknightion/meraki-dashboard-ha/commit/3e33b14fa79bb79b5430467f35709e2c9247df57))
* update translation documentation ([e9c6d94](https://github.com/rknightion/meraki-dashboard-ha/commit/e9c6d94460476c053903befefb31844ad981e9f3))


### Miscellaneous Chores

* add cache and stats config translations ([6ef0a69](https://github.com/rknightion/meraki-dashboard-ha/commit/6ef0a698296dc78b01704e041a0435bc5cac26c5))
* bits ([dabd294](https://github.com/rknightion/meraki-dashboard-ha/commit/dabd294bc550053655a2096478ecec4104d7261a))
* **core:** registry cleanup and unload hooks ([55e3f51](https://github.com/rknightion/meraki-dashboard-ha/commit/55e3f518f4e8f37c5be6e4c289897976ea56ba13))
* **deps:** lock file maintenance ([#227](https://github.com/rknightion/meraki-dashboard-ha/issues/227)) ([05b8a2e](https://github.com/rknightion/meraki-dashboard-ha/commit/05b8a2e9aeccd36d1cd4b16f00f5ccc42b1b6b70))
* **deps:** lock file maintenance ([#228](https://github.com/rknightion/meraki-dashboard-ha/issues/228)) ([c782913](https://github.com/rknightion/meraki-dashboard-ha/commit/c782913cf5c98c2aa8f12c07a52cb9f6e01acdc8))
* **deps:** update anthropics/claude-code-action digest to c9ec2b0 ([#229](https://github.com/rknightion/meraki-dashboard-ha/issues/229)) ([528d3a1](https://github.com/rknightion/meraki-dashboard-ha/commit/528d3a1dcc1558fd2753000556dd7ce44e870527))
* **deps:** update astral-sh/setup-uv action to v7.2.0 ([#230](https://github.com/rknightion/meraki-dashboard-ha/issues/230)) ([000a17c](https://github.com/rknightion/meraki-dashboard-ha/commit/000a17c862f869a93d007259c7a41c89d3e95b43))
* docs ([52f9583](https://github.com/rknightion/meraki-dashboard-ha/commit/52f9583a81c3d8e223c5c915773067e64b87116c))
* migrate changelog to docs directory ([80bcfcc](https://github.com/rknightion/meraki-dashboard-ha/commit/80bcfcccceb38703784b9a4fb986354a76364c55))
* secs ([9ba72d9](https://github.com/rknightion/meraki-dashboard-ha/commit/9ba72d98667a14e73cbe2884ebea6288d71c7893))
* updates ([f9eb060](https://github.com/rknightion/meraki-dashboard-ha/commit/f9eb0606e1b1aa0721c75a320541ed8df505e9d4))


### Code Refactoring

* **api:** async API call routing and batch invocation ([2135d11](https://github.com/rknightion/meraki-dashboard-ha/commit/2135d11e633faf230226824cbaabbc0a69291734))
* improve config flow hub settings UI ([7d107e0](https://github.com/rknightion/meraki-dashboard-ha/commit/7d107e043dc16e11aae50f67bc386e66032af5b0))

## [0.35.0](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.34.0...v0.35.0) (2025-12-22)


### Features

* add cache and batch API helpers ([88973f2](https://github.com/rknightion/meraki-dashboard-ha/commit/88973f26045b9a3fd619e345271e0f4822e5ff1a))
* add cache TTL config options ([89b1d2a](https://github.com/rknightion/meraki-dashboard-ha/commit/89b1d2adafd3b95479fe8c623dd74279ad1b394c))
* add config flow UI for cache settings ([902fecf](https://github.com/rknightion/meraki-dashboard-ha/commit/902fecf54892c0424da3de7580883a5bb0a5316c))
* optimize MR device data with caching ([f00ea17](https://github.com/rknightion/meraki-dashboard-ha/commit/f00ea176c876997058f188b1a6ddc042d4fdf5af))
* optimize MR statistics with caching ([45c3938](https://github.com/rknightion/meraki-dashboard-ha/commit/45c393818866a3cf3308fe741d27e846369e2e88))
* optimize MS device data with caching ([4a8f10d](https://github.com/rknightion/meraki-dashboard-ha/commit/4a8f10d969a09e4c9c26533fbbd4f058d331a77c))
* optimize MS statistics with caching ([84edb92](https://github.com/rknightion/meraki-dashboard-ha/commit/84edb92832d28b9d6915ea2b59fdea49135fff19))


### Documentation

* add cache and metric config help text ([9fbe466](https://github.com/rknightion/meraki-dashboard-ha/commit/9fbe466020489b51c883f68997200e46664fe94b))
* regenerate entity documentation ([7f8203c](https://github.com/rknightion/meraki-dashboard-ha/commit/7f8203ccee50f96ede49f8e05c01f31eb2beb9e4))


### Miscellaneous Chores

* claude ([f476702](https://github.com/rknightion/meraki-dashboard-ha/commit/f476702718dbbf7d63bf6c153a188bf0f9fef2b5))
* clean up config files and docs ([bdf72a0](https://github.com/rknightion/meraki-dashboard-ha/commit/bdf72a0262234624783377794b4bc1561d225441))
* **deps:** lock file maintenance ([#225](https://github.com/rknightion/meraki-dashboard-ha/issues/225)) ([482a8ab](https://github.com/rknightion/meraki-dashboard-ha/commit/482a8ab2df231970634734e2e659c69e16aea990))
* doc ([3959160](https://github.com/rknightion/meraki-dashboard-ha/commit/39591604b182c329ed00c2e24b9c5086deb90a0f))
* docfix ([4dc80f6](https://github.com/rknightion/meraki-dashboard-ha/commit/4dc80f65c0bc9ee61aa4bfb1d9e0d05f1a7f1483))
* fix docbuild ([5f540cb](https://github.com/rknightion/meraki-dashboard-ha/commit/5f540cbdaf53520e9f6e754365a9f538ace3ccc5))
* update dependencies and add zensical config ([392f85b](https://github.com/rknightion/meraki-dashboard-ha/commit/392f85b4101419a72341d1cb49a085a91259f162))

## [0.34.0](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.33.0...v0.34.0) (2025-12-20)


### Features

* add comprehensive startup summary with detailed hub information ([79040fc](https://github.com/rknightion/meraki-dashboard-ha/commit/79040fc4696a4632d1f57b377765daf6cac75fa3))
* add CW device support for wireless APs ([8b0491a](https://github.com/rknightion/meraki-dashboard-ha/commit/8b0491af98c030a47017b774ec1c0e20371a45e4)), closes [#218](https://github.com/rknightion/meraki-dashboard-ha/issues/218)
* add device type mapping system ([90e7bc2](https://github.com/rknightion/meraki-dashboard-ha/commit/90e7bc2c2b295a7cbce14bea7df73978795526a3))


### Documentation

* add agent guidance for meraki api documentation ([2281907](https://github.com/rknightion/meraki-dashboard-ha/commit/22819079f10e616863a038f37b1ef12388203aa5))
* add comprehensive todo list for integration improvements ([212fdee](https://github.com/rknightion/meraki-dashboard-ha/commit/212fdeedccccadc1f4d3f9756acbc03ffc35fe84))
* improve SEO meta tags robustness ([b1ea29d](https://github.com/rknightion/meraki-dashboard-ha/commit/b1ea29d143ff6c73c4d33f50b45836dfdb6636b2))


### Miscellaneous Chores

* **deps:** lock file maintenance ([#219](https://github.com/rknightion/meraki-dashboard-ha/issues/219)) ([99d7bb1](https://github.com/rknightion/meraki-dashboard-ha/commit/99d7bb1facf08459c2d58e1bfae5a54e05e40482))
* **deps:** update anthropics/claude-code-action digest to 0d19335 ([#221](https://github.com/rknightion/meraki-dashboard-ha/issues/221)) ([9afc269](https://github.com/rknightion/meraki-dashboard-ha/commit/9afc269bd3f7f4472053e7961b1ffb97e7f0af12))
* **deps:** update anthropics/claude-code-action digest to 7145c3e ([#222](https://github.com/rknightion/meraki-dashboard-ha/issues/222)) ([6b5e150](https://github.com/rknightion/meraki-dashboard-ha/commit/6b5e1507fd6e6982f9b1eb8ec085985fa52c1ab0))
* **deps:** update anthropics/claude-code-action digest to d7b6d50 ([#220](https://github.com/rknightion/meraki-dashboard-ha/issues/220)) ([4e6879d](https://github.com/rknightion/meraki-dashboard-ha/commit/4e6879d481aeca8dded4b3e1496a21b29c5eb222))
* **deps:** update dependency pytest-homeassistant-custom-component to v0.13.301 ([#223](https://github.com/rknightion/meraki-dashboard-ha/issues/223)) ([8a8f0cc](https://github.com/rknightion/meraki-dashboard-ha/commit/8a8f0cc43a2f0baabf8dd61e8c2df7c5c6e24d57))
* disable debug logging in dev config ([b74bfbf](https://github.com/rknightion/meraki-dashboard-ha/commit/b74bfbffcd838613768445bbf1dadfd4ce1e1bbc))
* remove documentation build dependencies and configuration ([36c4d13](https://github.com/rknightion/meraki-dashboard-ha/commit/36c4d1397b504628a350b3823386e4a40ece8ee7))
* tidy up unneded workflows ([f9a1fe4](https://github.com/rknightion/meraki-dashboard-ha/commit/f9a1fe4011b0ff981aa9ff6fdc1208444bb707c4))
* update development dependencies and container packages ([52a1b99](https://github.com/rknightion/meraki-dashboard-ha/commit/52a1b9901ad3a0b4f5ff6607f95e75a758a7639d))
* update documentation links and build configuration ([927af63](https://github.com/rknightion/meraki-dashboard-ha/commit/927af63d6fb4441e124ed1c7901fae7f0586fb8f))
* update secrets baseline timestamps ([25494a2](https://github.com/rknightion/meraki-dashboard-ha/commit/25494a2e10d74a57efdb7c840b92435758f175bb))


### Code Refactoring

* improve startup summary formatting ([f70acef](https://github.com/rknightion/meraki-dashboard-ha/commit/f70acef0453d2a496df74784649405a157629cd5))
* reduce logging verbosity for network hub operations ([fbb3a8e](https://github.com/rknightion/meraki-dashboard-ha/commit/fbb3a8e59485543f19ed806708c5f2e68682dc49))
* use centralized device type detection ([3dd91c7](https://github.com/rknightion/meraki-dashboard-ha/commit/3dd91c7c35e564c3dfd3b5cedfcf780a0fce8c8d))

## [0.33.0](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.32.3...v0.33.0) (2025-12-13)


### Features

* add control character sanitization to protect against database injection ([495c867](https://github.com/rknightion/meraki-dashboard-ha/commit/495c867600988d1db94fbca2d37f260d8407b293))
* apply sanitization to device sensor entity attributes ([43f3d91](https://github.com/rknightion/meraki-dashboard-ha/commit/43f3d9159be1e3c2018744b663e0137ba9faaa00))
* sanitize base entity attributes and device info ([69a0be6](https://github.com/rknightion/meraki-dashboard-ha/commit/69a0be6c959a2ec3ee1bb7cf9aeccb9103b015fc))


### Bug Fixes

* improve datetime handling and test framework usage ([b7c317c](https://github.com/rknightion/meraki-dashboard-ha/commit/b7c317c4ecf198b5a24bbc7158826c89dd06e71d))


### Documentation

* clarify HACS default repository availability ([830f014](https://github.com/rknightion/meraki-dashboard-ha/commit/830f014b38368c80e0c7d93b2aeaccc5771d7de1))


### Miscellaneous Chores

* **config:** migrate config renovate.json ([30fd40f](https://github.com/rknightion/meraki-dashboard-ha/commit/30fd40f957b4ce7d91436b16be7e38bd84e01fdf))
* **config:** migrate Renovate config ([c8dde03](https://github.com/rknightion/meraki-dashboard-ha/commit/c8dde03e8472351be857e0808ddced85d85bfc13))
* **deps:** lock file maintenance ([#167](https://github.com/rknightion/meraki-dashboard-ha/issues/167)) ([48a1af0](https://github.com/rknightion/meraki-dashboard-ha/commit/48a1af01ec11e724b020a35a9b14c04315feb338))
* **deps:** lock file maintenance ([#175](https://github.com/rknightion/meraki-dashboard-ha/issues/175)) ([9ffe528](https://github.com/rknightion/meraki-dashboard-ha/commit/9ffe528c95c342430b9990c49c11809746eaf23e))
* **deps:** lock file maintenance ([#185](https://github.com/rknightion/meraki-dashboard-ha/issues/185)) ([6814674](https://github.com/rknightion/meraki-dashboard-ha/commit/6814674d0dc945037393475da41f43407bde9fde))
* **deps:** lock file maintenance ([#190](https://github.com/rknightion/meraki-dashboard-ha/issues/190)) ([f6282c1](https://github.com/rknightion/meraki-dashboard-ha/commit/f6282c142ad5509267982fcbdbd048d41211ee2e))
* **deps:** lock file maintenance ([#201](https://github.com/rknightion/meraki-dashboard-ha/issues/201)) ([5075184](https://github.com/rknightion/meraki-dashboard-ha/commit/5075184394c50b549574b0ac26deeb6a51098c8d))
* **deps:** pin anthropics/claude-code-action action to 6337623 ([2406b54](https://github.com/rknightion/meraki-dashboard-ha/commit/2406b5441bdede89f6fc8e7f06e632cef5e9ed5f))
* **deps:** pin dependencies ([#204](https://github.com/rknightion/meraki-dashboard-ha/issues/204)) ([4fb04bf](https://github.com/rknightion/meraki-dashboard-ha/commit/4fb04bfdcf7223bcd0598d6cb62e83bfdde34287))
* **deps:** update actions/checkout action to v5.0.1 ([#177](https://github.com/rknightion/meraki-dashboard-ha/issues/177)) ([a202ad9](https://github.com/rknightion/meraki-dashboard-ha/commit/a202ad9264fea5ca3eda9265bcc6077d8f369551))
* **deps:** update actions/checkout action to v6 ([f2031e2](https://github.com/rknightion/meraki-dashboard-ha/commit/f2031e29f242675ebc7dd71edff86eb361ad1fa3))
* **deps:** update actions/checkout action to v6 ([#180](https://github.com/rknightion/meraki-dashboard-ha/issues/180)) ([3c5f3b5](https://github.com/rknightion/meraki-dashboard-ha/commit/3c5f3b502f527f490c3e8bb8e480b33e07598347))
* **deps:** update actions/checkout action to v6.0.1 ([#195](https://github.com/rknightion/meraki-dashboard-ha/issues/195)) ([8d57b9c](https://github.com/rknightion/meraki-dashboard-ha/commit/8d57b9cca4274deca6a09dacd7a4f76a932747c6))
* **deps:** update actions/checkout digest to 8e8c483 ([#194](https://github.com/rknightion/meraki-dashboard-ha/issues/194)) ([7cc4d04](https://github.com/rknightion/meraki-dashboard-ha/commit/7cc4d044666ef58c2d78c60689df80bd682bdbe1))
* **deps:** update actions/checkout digest to 93cb6ef ([#176](https://github.com/rknightion/meraki-dashboard-ha/issues/176)) ([1e54e95](https://github.com/rknightion/meraki-dashboard-ha/commit/1e54e959f10f293a053afe69393e89a0b305c750))
* **deps:** update actions/dependency-review-action action to v4.8.2 ([#169](https://github.com/rknightion/meraki-dashboard-ha/issues/169)) ([d4a04a3](https://github.com/rknightion/meraki-dashboard-ha/commit/d4a04a38124770e172de8126e0d1126423d6b3e2))
* **deps:** update actions/setup-python action to v6.1.0 ([#189](https://github.com/rknightion/meraki-dashboard-ha/issues/189)) ([9c5a02c](https://github.com/rknightion/meraki-dashboard-ha/commit/9c5a02c6e2248ef460dd34a1dde0159020fc8f0d))
* **deps:** update actions/stale action to v10.1.1 ([#196](https://github.com/rknightion/meraki-dashboard-ha/issues/196)) ([7ea4966](https://github.com/rknightion/meraki-dashboard-ha/commit/7ea49669e8d8e7798bbd65ad0df241942309e719))
* **deps:** update actions/upload-artifact action to v6 ([#213](https://github.com/rknightion/meraki-dashboard-ha/issues/213)) ([263e080](https://github.com/rknightion/meraki-dashboard-ha/commit/263e0809519c842b483e478f5eb817e35b40e7c3))
* **deps:** update anthropics/claude-code-action digest to f0c8eb2 ([#207](https://github.com/rknightion/meraki-dashboard-ha/issues/207)) ([81778e0](https://github.com/rknightion/meraki-dashboard-ha/commit/81778e02b81cf7bf689006aeb56674d456e6c0ad))
* **deps:** update astral-sh/setup-uv action to v7.1.3 ([#170](https://github.com/rknightion/meraki-dashboard-ha/issues/170)) ([36799a2](https://github.com/rknightion/meraki-dashboard-ha/commit/36799a280adae6bf91a95cc4ab236a183f6348bf))
* **deps:** update astral-sh/setup-uv action to v7.1.4 ([#181](https://github.com/rknightion/meraki-dashboard-ha/issues/181)) ([0de0a2b](https://github.com/rknightion/meraki-dashboard-ha/commit/0de0a2b097d6ac07326f0c831b122ab47388053a))
* **deps:** update astral-sh/setup-uv action to v7.1.5 ([#200](https://github.com/rknightion/meraki-dashboard-ha/issues/200)) ([87116bd](https://github.com/rknightion/meraki-dashboard-ha/commit/87116bdda43f335f080917db5ab1e6cc3de4b01c))
* **deps:** update astral-sh/setup-uv action to v7.1.6 ([#214](https://github.com/rknightion/meraki-dashboard-ha/issues/214)) ([7fe7134](https://github.com/rknightion/meraki-dashboard-ha/commit/7fe71340f5299713450a17cb5a5a28bb4fadcc32))
* **deps:** update codecov/codecov-action action to v5.5.2 ([#208](https://github.com/rknightion/meraki-dashboard-ha/issues/208)) ([34d5872](https://github.com/rknightion/meraki-dashboard-ha/commit/34d5872f3df41afdec6a95c9d2abbeb3f70f6f83))
* **deps:** update dependency homeassistant-stubs to v2025.11.2 ([#174](https://github.com/rknightion/meraki-dashboard-ha/issues/174)) ([5bd8162](https://github.com/rknightion/meraki-dashboard-ha/commit/5bd8162e207eacc7d6048726dfa755f6d2361b28))
* **deps:** update dependency homeassistant-stubs to v2025.11.3 ([#183](https://github.com/rknightion/meraki-dashboard-ha/issues/183)) ([f2bbe6d](https://github.com/rknightion/meraki-dashboard-ha/commit/f2bbe6d501cde7f6d77d581626a8686069df43af))
* **deps:** update dependency homeassistant-stubs to v2025.12.1 ([6650e6f](https://github.com/rknightion/meraki-dashboard-ha/commit/6650e6f1e18af64edfa53ccaed6c298c4bfdb77e))
* **deps:** update dependency pytest-homeassistant-custom-component to v0.13.300 ([a861cb3](https://github.com/rknightion/meraki-dashboard-ha/commit/a861cb3247473ddb847587759d7ccb205e37752d))
* **deps:** update dependency pytest-homeassistant-custom-component to v0.13.300 ([da74251](https://github.com/rknightion/meraki-dashboard-ha/commit/da742518ef03535ebb7d87de32fa9651d887a795))
* **deps:** update github/codeql-action action to v4.31.3 ([#172](https://github.com/rknightion/meraki-dashboard-ha/issues/172)) ([faf682a](https://github.com/rknightion/meraki-dashboard-ha/commit/faf682aea77e689ace7821b42ed768308c9169cd))
* **deps:** update github/codeql-action action to v4.31.4 ([#179](https://github.com/rknightion/meraki-dashboard-ha/issues/179)) ([1a85f18](https://github.com/rknightion/meraki-dashboard-ha/commit/1a85f18033183b8ed51b47d3942cf8d72a66d87c))
* **deps:** update github/codeql-action action to v4.31.5 ([#188](https://github.com/rknightion/meraki-dashboard-ha/issues/188)) ([88964fb](https://github.com/rknightion/meraki-dashboard-ha/commit/88964fbee566ad0453b595423e173709c8a59d78))
* **deps:** update github/codeql-action action to v4.31.6 ([#192](https://github.com/rknightion/meraki-dashboard-ha/issues/192)) ([cfd49fc](https://github.com/rknightion/meraki-dashboard-ha/commit/cfd49fcdb2318c9a35a986b7cef4a6d76f99d0ad))
* **deps:** update github/codeql-action action to v4.31.7 ([#199](https://github.com/rknightion/meraki-dashboard-ha/issues/199)) ([a9e8125](https://github.com/rknightion/meraki-dashboard-ha/commit/a9e8125af770fc8d2c0451fa7491dfc166fd9bec))
* **deps:** update github/codeql-action action to v4.31.8 ([#212](https://github.com/rknightion/meraki-dashboard-ha/issues/212)) ([d5c78bb](https://github.com/rknightion/meraki-dashboard-ha/commit/d5c78bb1bbe9be451ae53ca2456b27a0e6d7b058))
* **deps:** update github/codeql-action digest to 014f16e ([#171](https://github.com/rknightion/meraki-dashboard-ha/issues/171)) ([432ba25](https://github.com/rknightion/meraki-dashboard-ha/commit/432ba25417d1649ccc089be3163bd2a41949bb83))
* **deps:** update github/codeql-action digest to 1b168cd ([#211](https://github.com/rknightion/meraki-dashboard-ha/issues/211)) ([d7d44c2](https://github.com/rknightion/meraki-dashboard-ha/commit/d7d44c2cad2350dd7e796d864b8f1607d339b00a))
* **deps:** update github/codeql-action digest to cf1bb45 ([#198](https://github.com/rknightion/meraki-dashboard-ha/issues/198)) ([a0d8f97](https://github.com/rknightion/meraki-dashboard-ha/commit/a0d8f97cb0b5d3f63bbad8b0935c2d86771fd992))
* **deps:** update github/codeql-action digest to e12f017 ([#178](https://github.com/rknightion/meraki-dashboard-ha/issues/178)) ([724bfa9](https://github.com/rknightion/meraki-dashboard-ha/commit/724bfa91dce1d272099f18a9e20164548ca1f784))
* **deps:** update github/codeql-action digest to fdbfb4d ([#187](https://github.com/rknightion/meraki-dashboard-ha/issues/187)) ([14fc149](https://github.com/rknightion/meraki-dashboard-ha/commit/14fc14958d67400d389453494724b9864301d675))
* **deps:** update github/codeql-action digest to fe4161a ([#191](https://github.com/rknightion/meraki-dashboard-ha/issues/191)) ([f0a03ad](https://github.com/rknightion/meraki-dashboard-ha/commit/f0a03ad6650344f7614ddcff2c6e6f6c3b61e7bf))
* **deps:** update home-assistant/actions digest to 01a62fa ([#182](https://github.com/rknightion/meraki-dashboard-ha/issues/182)) ([e87c06f](https://github.com/rknightion/meraki-dashboard-ha/commit/e87c06f5aefd4940e572363a1c7c74a16a9e15e8))
* **deps:** update home-assistant/actions digest to 6778c32 ([#186](https://github.com/rknightion/meraki-dashboard-ha/issues/186)) ([260c9bb](https://github.com/rknightion/meraki-dashboard-ha/commit/260c9bb9138b27783835a58d5e824dad18ed0395))
* **deps:** update home-assistant/actions digest to 87c064c ([#202](https://github.com/rknightion/meraki-dashboard-ha/issues/202)) ([9b076b0](https://github.com/rknightion/meraki-dashboard-ha/commit/9b076b0fcdb2fffa8f2cfa2e9b3391c5235f6855))
* **deps:** update peter-evans/repository-dispatch digest to 28959ce ([#173](https://github.com/rknightion/meraki-dashboard-ha/issues/173)) ([c0797c7](https://github.com/rknightion/meraki-dashboard-ha/commit/c0797c7a2a0f9fc7d5ea54ec9fb99ca72e3b201b))
* **deps:** update step-security/harden-runner action to v2.13.3 ([#193](https://github.com/rknightion/meraki-dashboard-ha/issues/193)) ([3b6c1f4](https://github.com/rknightion/meraki-dashboard-ha/commit/3b6c1f486170d79e2288b7b51efd751600c61fb2))
* **deps:** update step-security/harden-runner action to v2.14.0 ([#210](https://github.com/rknightion/meraki-dashboard-ha/issues/210)) ([50b5f55](https://github.com/rknightion/meraki-dashboard-ha/commit/50b5f55d4f443e9b0fc153f18692afd3735f6869))
* **deps:** update zizmorcore/zizmor-action action to v0.3.0 ([#184](https://github.com/rknightion/meraki-dashboard-ha/issues/184)) ([23c1a43](https://github.com/rknightion/meraki-dashboard-ha/commit/23c1a43a8f49bab163c34d2abea370034a54fb97))
* override pytest constraint in meraki dependency ([e21b78d](https://github.com/rknightion/meraki-dashboard-ha/commit/e21b78d7a8d025bcf20237dcf4f1d2e786643683))
* **seo:** add comprehensive SEO enhancements for Home Assistant integration docs ([957b7a9](https://github.com/rknightion/meraki-dashboard-ha/commit/957b7a90e6fe25394167315275496018c8b90286))
* update development dependencies and package versions ([baa77bc](https://github.com/rknightion/meraki-dashboard-ha/commit/baa77bca7e82b53fba6f9f32532a3fc05a6a613b))
* update urllib3 dependency from 2.6.0 to 2.6.1 ([fe2f130](https://github.com/rknightion/meraki-dashboard-ha/commit/fe2f130758ca20dfef5dce345b92712741e2e34a))

## [0.32.3](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.32.2...v0.32.3) (2025-11-08)


### Miscellaneous Chores

* **deps:** update dependency homeassistant-stubs to v2025.11.1 ([#164](https://github.com/rknightion/meraki-dashboard-ha/issues/164)) ([c0264f0](https://github.com/rknightion/meraki-dashboard-ha/commit/c0264f0c70257b546d0f4e0eff00e97e08373dc2))


### Code Refactoring

* **ci:** fix zip creation process in release workflow ([43fcd0a](https://github.com/rknightion/meraki-dashboard-ha/commit/43fcd0ab38d178e860b10ae4a51ba4f425451c07))

## [0.32.2](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.32.1...v0.32.2) (2025-11-08)


### Miscellaneous Chores

* **deps:** update dbus-fast to version 2.44.6 ([d3650cc](https://github.com/rknightion/meraki-dashboard-ha/commit/d3650cc04df60a9ef46c7a900468aeced517d49c))

## [0.32.1](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.32.0...v0.32.1) (2025-11-07)


### Miscellaneous Chores

* deps ([3ac803a](https://github.com/rknightion/meraki-dashboard-ha/commit/3ac803a3eab7003de620ae20ad953106d89572eb))

## [0.32.0](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.31.0...v0.32.0) (2025-11-07)


### Features

* add automatic energy sensors for MT devices ([4a06d8f](https://github.com/rknightion/meraki-dashboard-ha/commit/4a06d8feaba16fe2d69603296088185fed0653fb)), closes [#123](https://github.com/rknightion/meraki-dashboard-ha/issues/123)
* add comprehensive VS Code debug configurations for Home Assistant development ([df0d76c](https://github.com/rknightion/meraki-dashboard-ha/commit/df0d76c134185662dd6ccfb9adb427fd5d528c37))
* add configurable API base URL and improve logging ([6f6c022](https://github.com/rknightion/meraki-dashboard-ha/commit/6f6c02223e1770771c39f845259a465d63e6861b)), closes [#123](https://github.com/rknightion/meraki-dashboard-ha/issues/123)
* Add configurable tiered refresh intervals for data ([bf02f0b](https://github.com/rknightion/meraki-dashboard-ha/commit/bf02f0bdf1986e8bdfbd089a580dd1460288eab9))
* add daily Jekyll deployment schedule ([4a98467](https://github.com/rknightion/meraki-dashboard-ha/commit/4a98467abab801e9011e65d6336c0ac8750f9878))
* add device type filtering options ([aa2f0af](https://github.com/rknightion/meraki-dashboard-ha/commit/aa2f0afe1f71221944ccbc10d424a4e6a17d2790))
* add diagnostics and repair flows for Meraki Dashboard integration ([d87eee5](https://github.com/rknightion/meraki-dashboard-ha/commit/d87eee563f20403964ed068f0adade1b5364d1d1))
* add fixable attribute to error messages ([7b1cebf](https://github.com/rknightion/meraki-dashboard-ha/commit/7b1cebf4d3ab0ff4e9989adacf1794b41db34685))
* add historical data handling and coordinator enhancements ([8b2ef44](https://github.com/rknightion/meraki-dashboard-ha/commit/8b2ef444702a1afdaf98df50ac9fb1e07f3ac799))
* add memory usage metrics for MR and MS devices ([b91ec46](https://github.com/rknightion/meraki-dashboard-ha/commit/b91ec466af4c9a44688b632d3cc67d80a2d62dda))
* add MT refresh service configuration and interval validation ([d86ffa7](https://github.com/rknightion/meraki-dashboard-ha/commit/d86ffa7eadf93dd61344e2cb17a3ba5918643c27))
* add new sensors for Meraki MR and MS devices ([e52a9d6](https://github.com/rknightion/meraki-dashboard-ha/commit/e52a9d6dcffba1136cb6e88d9389bb02095167df))
* add organization-level ethernet status caching for wireless devices ([d07e68a](https://github.com/rknightion/meraki-dashboard-ha/commit/d07e68a37ffa8b2fd916a45bdaf944cd8a1ef9f9))
* add USB Powered binary sensor support ([17d7b23](https://github.com/rknightion/meraki-dashboard-ha/commit/17d7b2337d40cb85fe7d0bf8f05f1d062010259b))
* add VS Code workspace settings template for Home Assistant development ([aada45a](https://github.com/rknightion/meraki-dashboard-ha/commit/aada45a0f28f7597a4f3b74586a17ccfd63bab0d))
* Adds Bluetooth clients sensor and related data handling ([4203748](https://github.com/rknightion/meraki-dashboard-ha/commit/42037486b55889c288a47bc0d13af9d42f249b62))
* **api:** increase MR and MS device refresh intervals to 10 minutes ([d0e53e5](https://github.com/rknightion/meraki-dashboard-ha/commit/d0e53e5e6131616b9f3404a6335c7420e2624e4d))
* auto-run release notes generation on pushes to main ([1c7ceb7](https://github.com/rknightion/meraki-dashboard-ha/commit/1c7ceb7b1b9015b18ac9214e95df0895cdde11d5))
* auto-trigger Jekyll deployment after changelog updates ([b713888](https://github.com/rknightion/meraki-dashboard-ha/commit/b7138880300e3b3bae5528d9b066a2a5b0c287f5))
* **config:** initialize domain and add manifest ([b8258f3](https://github.com/rknightion/meraki-dashboard-ha/commit/b8258f35667a004365c5c31262be503342bf3f6d))
* Enable automatic application of API guidelines and code style rules ([715dc99](https://github.com/rknightion/meraki-dashboard-ha/commit/715dc994c1924ea380c99e65f88754980a6ef0d4))
* enhance changelog and release configuration ([5242fe1](https://github.com/rknightion/meraki-dashboard-ha/commit/5242fe1538c15c3ad68a0b258dc8dff17131b750))
* enhance config flow with MT refresh settings and improved UX ([72f4fd5](https://github.com/rknightion/meraki-dashboard-ha/commit/72f4fd5f23829323e8da0ca64d469b2806d2ccba))
* enhance device monitoring and traffic handling ([0853961](https://github.com/rknightion/meraki-dashboard-ha/commit/08539610ac139b48b6c67af7eff8d908c22d5d43))
* Enhance device status information retrieval ([f23a7eb](https://github.com/rknightion/meraki-dashboard-ha/commit/f23a7ebf5d225749c3be247fcf04a1be5723a642))
* enhance energy sensor precision and add reset logic ([3db1459](https://github.com/rknightion/meraki-dashboard-ha/commit/3db145979008b8da083a5532b6b55f48bfb7e62b))
* enhance error logging and improve statistic handling ([04827fd](https://github.com/rknightion/meraki-dashboard-ha/commit/04827fd134a2d3a463bfccf349cd11451e239329))
* enhance Home Assistant development configuration ([57f7a0a](https://github.com/rknightion/meraki-dashboard-ha/commit/57f7a0a23d557251cc7a6b54fc3f1e02538aba63))
* enhance logging and discovery configurations ([3a44805](https://github.com/rknightion/meraki-dashboard-ha/commit/3a4480520f72bc77dca87b28987e911bef753516)), closes [#123](https://github.com/rknightion/meraki-dashboard-ha/issues/123)
* enhance release note generation for direct commits ([e61bd2c](https://github.com/rknightion/meraki-dashboard-ha/commit/e61bd2ca4edeb2caa6a9155884c7278f5c7cc7ce))
* enhance sensor update with live and historical data ([d6201bb](https://github.com/rknightion/meraki-dashboard-ha/commit/d6201bb81c1b00243fc2df5a39170849f9e22cca))
* enhance version update workflow ([5743c48](https://github.com/rknightion/meraki-dashboard-ha/commit/5743c486eaf6e46e8e0df1b0ddff1a73c2f226d1))
* expand device type support in device selection flow ([231b5f6](https://github.com/rknightion/meraki-dashboard-ha/commit/231b5f685923d5b03dbe4cc0a790a618049ba8e7))
* historical data collection ([41165a8](https://github.com/rknightion/meraki-dashboard-ha/commit/41165a88e1155be2c40cd004668366c3ed011416))
* **i18n:** enhance user interface strings with detailed descriptions and MT sensor support ([3818d4a](https://github.com/rknightion/meraki-dashboard-ha/commit/3818d4a899a92eb67b5529bef037af59974bf4be))
* implement configurable MT refresh service with interval support ([f591616](https://github.com/rknightion/meraki-dashboard-ha/commit/f591616021b019dbae8626677564af44aae7e3cb))
* implement dynamic MT device capability discovery ([7817f1c](https://github.com/rknightion/meraki-dashboard-ha/commit/7817f1c5d535daec52a20aae27ee41c28ebf0947))
* improve graceful handling of missing sensor readings ([c01b38e](https://github.com/rknightion/meraki-dashboard-ha/commit/c01b38e6e14509849544654e2bbba425dfb0d14f))
* Introduces Meraki Dashboard integration with multi-device support ([ea6d2d8](https://github.com/rknightion/meraki-dashboard-ha/commit/ea6d2d899897833d95b41494cd8c9b0e8685cee2))
* **mt:** implement fast refresh mode for MT15/MT40 devices ([54ddccd](https://github.com/rknightion/meraki-dashboard-ha/commit/54ddccdf8d9b5785bd805803eca2002841eb7ae1))
* **options:** improve device-specific configuration UI ([26e2afc](https://github.com/rknightion/meraki-dashboard-ha/commit/26e2afca68b7a07e86f77d5d9053c3201b18a1ca))
* remove all-checks-pass job and update dependencies ([1f546e6](https://github.com/rknightion/meraki-dashboard-ha/commit/1f546e6a5f62c594e69e4de6d39aad9693998873)), closes [#789](https://github.com/rknightion/meraki-dashboard-ha/issues/789)
* remove duplicate statistics and adjust power factor representation ([62c87e3](https://github.com/rknightion/meraki-dashboard-ha/commit/62c87e3a05afca7b1626eb3d540233e392c2f6d0)), closes [#123](https://github.com/rknightion/meraki-dashboard-ha/issues/123)
* remove redundant 'fixable' attribute from strings ([a24b85d](https://github.com/rknightion/meraki-dashboard-ha/commit/a24b85d122c45b0b89e141a81f36d2b24dacb598))
* revamp documentation structure and update workflows ([aa3dede](https://github.com/rknightion/meraki-dashboard-ha/commit/aa3dede97ee5d1e81d479bb7ca61dc561eeae1e4)), closes [#185](https://github.com/rknightion/meraki-dashboard-ha/issues/185)
* **workflow:** enable auto-merge for release PRs ([064dbf9](https://github.com/rknightion/meraki-dashboard-ha/commit/064dbf9d083b66d5d29c4b11e2698ab3ccf59c89))
* **workflow:** enhance release process with asset management ([3e2b3a4](https://github.com/rknightion/meraki-dashboard-ha/commit/3e2b3a45bb9c283242ac85eedd12e41720e6da44))


### Bug Fixes

* add checkout step to enable auto-merge ([e527f6d](https://github.com/rknightion/meraki-dashboard-ha/commit/e527f6dc8532218f0b8a6c8a841ffce39f6130a4))
* add delay to prevent premature PR merge checks ([1df72a7](https://github.com/rknightion/meraki-dashboard-ha/commit/1df72a7194c92edd6d9354cfb2ecaf6ccf784a40))
* add some sleeps ([30c553d](https://github.com/rknightion/meraki-dashboard-ha/commit/30c553d7390cf50ffb11543efb6966bc49a4a075))
* address duplicate statistics in Meraki integration ([6d5a244](https://github.com/rknightion/meraki-dashboard-ha/commit/6d5a2448f0a1b9003e6eff8182bc168af4550097)), closes [#1234](https://github.com/rknightion/meraki-dashboard-ha/issues/1234)
* adjust minimum scan interval to 30 seconds for better responsiveness ([6ff4d0c](https://github.com/rknightion/meraki-dashboard-ha/commit/6ff4d0c41fbe8df0754efd1c332928f69a6bb032))
* Adjust test file patterns and convert energy units to kWh ([f5dc7e2](https://github.com/rknightion/meraki-dashboard-ha/commit/f5dc7e2d3848e066581498f24e57eaf1a3a45b8b))
* adjust version update and energy sensor logic ([0dcf06f](https://github.com/rknightion/meraki-dashboard-ha/commit/0dcf06fe090d2e1f368ec14df964dba0c4695cd6))
* adjust workflow for release events ([8b76cab](https://github.com/rknightion/meraki-dashboard-ha/commit/8b76cab7f01c9f73925673876b1f5377b7ef0557))
* codecov ([d9dbcbd](https://github.com/rknightion/meraki-dashboard-ha/commit/d9dbcbd29f65136ea22cae56960174bf2aafaa12))
* **config:** refine config flow domain initialization ([712fd33](https://github.com/rknightion/meraki-dashboard-ha/commit/712fd330d9c8032b58448c660a650305da3aef1e))
* consolidate release workflows and fix auto-merge logic ([72605d3](https://github.com/rknightion/meraki-dashboard-ha/commit/72605d307762848022fd72a89f1e55732d7700b7))
* convert energy state from kWh to Wh during restoration ([8bbe29f](https://github.com/rknightion/meraki-dashboard-ha/commit/8bbe29f4fb12ac6ad4b8d9abbd9dddacfb11341e))
* correct dictionary key access for data sorting ([333555d](https://github.com/rknightion/meraki-dashboard-ha/commit/333555dfa8235a61e227fbddc1cbb1edadb0a219))
* correct variable interpolation in GitHub workflows ([c4f2693](https://github.com/rknightion/meraki-dashboard-ha/commit/c4f2693bc0de9c4e3c13ebde1e931ae5de52e59e))
* correct water sensor data extraction and add memory usage metrics ([b5f90f8](https://github.com/rknightion/meraki-dashboard-ha/commit/b5f90f83cdbfce7ebb1b6ffcb98d52511622bc6a))
* **energy:** optimize energy calculation with data change detection ([da617bb](https://github.com/rknightion/meraki-dashboard-ha/commit/da617bb59201b942df9f3aabcd88642ee0385e60))
* enhance duplicate statistics cleanup description ([c2c5dfc](https://github.com/rknightion/meraki-dashboard-ha/commit/c2c5dfcb60d97080d59e29b23d1ded8a203024f7))
* Enhance performance and consistency in Meraki integration ([3a4f2fa](https://github.com/rknightion/meraki-dashboard-ha/commit/3a4f2fae8b8239b1d3cd3265c02b748d3bcbeb1f))
* enhance release workflow and remove obsolete sensor ([2a8ce0f](https://github.com/rknightion/meraki-dashboard-ha/commit/2a8ce0f681f65eb7d1e5232a8d978b7a9b2f3ade))
* ensure compatibility with older HA versions ([5c5a4cd](https://github.com/rknightion/meraki-dashboard-ha/commit/5c5a4cd76082e1daf882dad7429445808bea7f51))
* ensure version updates happen on main branch ([3673680](https://github.com/rknightion/meraki-dashboard-ha/commit/3673680cd68de17187d9ddcf112aa784b44c62af))
* fix indentation in GitHub release body template ([6b89aea](https://github.com/rknightion/meraki-dashboard-ha/commit/6b89aea5cc5122b0125e67cfb2a9df1bebd91dd3))
* fresh checkout before Jekyll deployment to include updated changelog ([e68ebf3](https://github.com/rknightion/meraki-dashboard-ha/commit/e68ebf35e6850831e0b71d7bf7d1f026b95f6897))
* gh pages maybe ([7e1fdd4](https://github.com/rknightion/meraki-dashboard-ha/commit/7e1fdd4c63789b23042f95003cdd252f86870067))
* **github-actions:** update permissions and config references ([88bde65](https://github.com/rknightion/meraki-dashboard-ha/commit/88bde65b1cf8bd3e3b32e7b96942d364ed49c677))
* handle existing tags in release note generation ([ade73b9](https://github.com/rknightion/meraki-dashboard-ha/commit/ade73b959d115c81a5ddd31681ac923c6486951b))
* improve auto-merge command for release PRs ([884cd2c](https://github.com/rknightion/meraki-dashboard-ha/commit/884cd2c6eb981fa16b70da07f259f00b191cd40d))
* improve configuration migration process ([a0dbdb0](https://github.com/rknightion/meraki-dashboard-ha/commit/a0dbdb0377f0d7d5c5c1adf0311176fe2fa853e0))
* improve GitHub Actions authentication for workflows ([59a7404](https://github.com/rknightion/meraki-dashboard-ha/commit/59a74040a70ee0339798deb9a206b542304ba519))
* improve reauth flow entry lookup mechanism ([f5a2353](https://github.com/rknightion/meraki-dashboard-ha/commit/f5a235349c3bb8c10b9ca9b008df2051ba4db3a9))
* include missing env var for release assets ([0a39bd3](https://github.com/rknightion/meraki-dashboard-ha/commit/0a39bd3e8585c36acb588cc1f4bca9b2f4e18d56))
* integrate Jekyll deployment directly into release workflow ([bcfc80a](https://github.com/rknightion/meraki-dashboard-ha/commit/bcfc80a5b92869b35aba39025dd7264d89fc3887))
* manual sleepz ([0c4bda2](https://github.com/rknightion/meraki-dashboard-ha/commit/0c4bda27c311ba5f46c0707d3c0fd336bcd793df))
* **mt-devices:** increase minimum update interval from 7.5s to 30s ([a76eaad](https://github.com/rknightion/meraki-dashboard-ha/commit/a76eaad6732cc4acb7fd634ba38b21b1b9cc61c4))
* ordering ([f5c0011](https://github.com/rknightion/meraki-dashboard-ha/commit/f5c00115d965f6a95098c800e2796c3ef6d2938c))
* Pin pytest-asyncio version ([1afa3d2](https://github.com/rknightion/meraki-dashboard-ha/commit/1afa3d2c42261d2400d1bc2c2d166f6e82241c6c))
* pr labeller ([a747a02](https://github.com/rknightion/meraki-dashboard-ha/commit/a747a0216d8229df63209fa732ce09891a5f4224))
* reduce scan and refresh intervals to 1 minute ([fc7b9ad](https://github.com/rknightion/meraki-dashboard-ha/commit/fc7b9adf9b36c82b304325dc1fd0068af585a690))
* Refactor and improve project structure and documentation ([5b5f58c](https://github.com/rknightion/meraki-dashboard-ha/commit/5b5f58c8ab882841a942abe517ef4602574aaa46))
* refactor sensor via_device identification ([5a278ae](https://github.com/rknightion/meraki-dashboard-ha/commit/5a278ae9a7b4e433bf549d35dc8698e816e9bae4))
* release ([397069d](https://github.com/rknightion/meraki-dashboard-ha/commit/397069d449e1ce127e1467c01ece5dd9d4406d8e))
* release notes generation with reliable versioning ([cf2adf4](https://github.com/rknightion/meraki-dashboard-ha/commit/cf2adf4141c1071a3e03adb09f9235ccec7dd73d))
* remove await from async_add_external_statistics call ([34c1ab6](https://github.com/rknightion/meraki-dashboard-ha/commit/34c1ab6b0d159587c9647e169d5be27fb52b4d4c))
* remove duplicate statistics check and repair flow ([92b1932](https://github.com/rknightion/meraki-dashboard-ha/commit/92b1932d316c4723913d054403620f4a5b0ea32c))
* Remove quotes from heredoc to allow variable interpolation ([fe1a216](https://github.com/rknightion/meraki-dashboard-ha/commit/fe1a2167dc46e562a586136f9ceafa0963a67fcf))
* remove self-approval from release-please workflow ([3913cd7](https://github.com/rknightion/meraki-dashboard-ha/commit/3913cd7b4ea03e03ab5f3a7927be888e2efd899b))
* reset release-please manifest to sync with actual releases ([be4ba25](https://github.com/rknightion/meraki-dashboard-ha/commit/be4ba2567b4ebdf3ee8036dc2e7bdbf28928a1ef))
* reset release-please state to bypass stuck 0.13.0 ([b968caa](https://github.com/rknightion/meraki-dashboard-ha/commit/b968caa6e11ceafdeda3e8e2e81cae910605b494))
* resolve workflow conflicts and shell injection issues ([f02026e](https://github.com/rknightion/meraki-dashboard-ha/commit/f02026e0086a8f64494c0f85c43f454f2be6a5ae))
* rp ([828c8dc](https://github.com/rknightion/meraki-dashboard-ha/commit/828c8dcb5c396b428410774de6dcd555b11c15f8))
* rp ([5ebd728](https://github.com/rknightion/meraki-dashboard-ha/commit/5ebd7282d53dd8d892efeab24f3e4f1a9983405d))
* rp ([e775542](https://github.com/rknightion/meraki-dashboard-ha/commit/e77554265297281eedee8e5b76285f88e0935ab8))
* rp ([a34ea74](https://github.com/rknightion/meraki-dashboard-ha/commit/a34ea7474ca0cfcb3069208ae9bdd1580009ca2b))
* rp ([d800970](https://github.com/rknightion/meraki-dashboard-ha/commit/d80097019f5702a417b864a3958067311270ba67))
* rp ([31d5bd5](https://github.com/rknightion/meraki-dashboard-ha/commit/31d5bd54be454aaa9740252cbbb50d26ccedf6ef))
* rp ([9d864ac](https://github.com/rknightion/meraki-dashboard-ha/commit/9d864acda1f77bfd24c352d99337cccf96a9643a))
* **sensors:** correct MT device model capabilities mapping ([c93df09](https://github.com/rknightion/meraki-dashboard-ha/commit/c93df096fbced5ef261f97ee500547828f56e392))
* **sensors:** fox indoor air quality support and expand fallback capabilities ([9255697](https://github.com/rknightion/meraki-dashboard-ha/commit/92556974ab9b7304c3827b621afafe4786c2ffc2))
* **sensor:** update TVOC unit to micrograms per cubic meter ([9e4be93](https://github.com/rknightion/meraki-dashboard-ha/commit/9e4be93bf2e2103f85a7400dd682a8d47d81c5d3)), closes [#123](https://github.com/rknightion/meraki-dashboard-ha/issues/123)
* test ([104d043](https://github.com/rknightion/meraki-dashboard-ha/commit/104d0432678e5652de7f7169c663f3000a4ed467))
* typo ([93b81a7](https://github.com/rknightion/meraki-dashboard-ha/commit/93b81a7a3fd84e6ec8ae2e0c6c5a3ac686ef0048))
* update formatting of strings in JSON ([19b37e5](https://github.com/rknightion/meraki-dashboard-ha/commit/19b37e5d2ea9d3e7d36cac44aef0b6925d379281))
* update measurement units and improve event logging ([67d53c7](https://github.com/rknightion/meraki-dashboard-ha/commit/67d53c72ef088b43c4eb05cc6a695c4d3f5e66e5))
* update permissions and add checkout step ([820b9e1](https://github.com/rknightion/meraki-dashboard-ha/commit/820b9e1afce9bc5022aa6fd3e2201b1cf5c30d0b))
* update release drafter to capture direct commits and enable manual trigger ([a78287d](https://github.com/rknightion/meraki-dashboard-ha/commit/a78287d1bd2b4a1bdb0615851a49800e8d8282af))
* update release-please manifest to acknowledge v0.13.0 release ([5734f94](https://github.com/rknightion/meraki-dashboard-ha/commit/5734f94e2fd7b3dcfc8a47ebeab8a6893b34e7da))
* update tests to match corrected MT device capabilities ([328f6eb](https://github.com/rknightion/meraki-dashboard-ha/commit/328f6eb75dcbb6b92198a21303c4c92360d7c66e))


### Performance Improvements

* optimize caching strategy in network hub data retrieval ([2dbc5e4](https://github.com/rknightion/meraki-dashboard-ha/commit/2dbc5e46114013aca6cd227bd0be2d0311493f9c))


### Documentation

* add AGENTS.md with project guidelines and architecture ([b57b8c3](https://github.com/rknightion/meraki-dashboard-ha/commit/b57b8c3ad2d2e2fec8d1817d1a08359e05f4dfc7))
* fix documentation links and update Cloudflare domain ([a28ca46](https://github.com/rknightion/meraki-dashboard-ha/commit/a28ca46e0ab025aab186d95a78a6d29339446f6e))
* restructure documentation with focused CLAUDE.md guidance ([63c4bbf](https://github.com/rknightion/meraki-dashboard-ha/commit/63c4bbf93399af8e16e4e08bb1695f0603120857))
* update CHANGELOG.md for release 0.24.7 ([9004afb](https://github.com/rknightion/meraki-dashboard-ha/commit/9004afb65f84216b3ac95d676aef98182d14889c))
* update mermaid diagram syntax in documentation ([9cf572e](https://github.com/rknightion/meraki-dashboard-ha/commit/9cf572edbc11df429cdc637b127afd05d9d9b4f0))


### Miscellaneous Chores

* add secrets baseline configuration for security scanning ([a1936f4](https://github.com/rknightion/meraki-dashboard-ha/commit/a1936f4d10a63b320eda3dd0619e1bd4b55e4ecc))
* change license from MIT to Apache 2.0 ([90f7bdb](https://github.com/rknightion/meraki-dashboard-ha/commit/90f7bdbf7a9d0927c3f38eb6eaa8e9e32fbef9af))
* **deps:** bump actions/ai-inference from 1.2.3 to 1.2.4 ([679fe2b](https://github.com/rknightion/meraki-dashboard-ha/commit/679fe2b3c55e4c2a730c170bdc0e1a6286d26c17))
* **deps:** bump actions/ai-inference from 1.2.3 to 1.2.4 ([ee1930b](https://github.com/rknightion/meraki-dashboard-ha/commit/ee1930b1078ac5a69bc39a74deed15c6758e82df))
* **deps:** bump actions/ai-inference from 1.2.4 to 1.2.7 ([58a345a](https://github.com/rknightion/meraki-dashboard-ha/commit/58a345a64f8dd4886698f759b25f9f0e2dfc62d3))
* **deps:** bump actions/ai-inference from 1.2.4 to 1.2.7 ([b8fcb12](https://github.com/rknightion/meraki-dashboard-ha/commit/b8fcb129e91093ba586282de0ae723f3c8da1f6c))
* **deps:** bump actions/ai-inference from 1.2.7 to 1.2.8 ([62e50d3](https://github.com/rknightion/meraki-dashboard-ha/commit/62e50d34d5a4d57d2a864d1b7abb7fe9a5614e1e))
* **deps:** bump actions/ai-inference from 1.2.7 to 1.2.8 ([b604f13](https://github.com/rknightion/meraki-dashboard-ha/commit/b604f13cdfaf6e517e4c5b614de4d004c2d82610))
* **deps:** bump actions/ai-inference from 1.2.8 to 2.0.0 ([57b1564](https://github.com/rknightion/meraki-dashboard-ha/commit/57b1564ef7090875cb80b6f31b8d855c934cd0bc))
* **deps:** bump actions/checkout from 4 to 5 ([3016abf](https://github.com/rknightion/meraki-dashboard-ha/commit/3016abf0369d6f30a595ab7e30227e996e7cc394))
* **deps:** bump actions/dependency-review-action from 4.7.1 to 4.7.2 ([85b0976](https://github.com/rknightion/meraki-dashboard-ha/commit/85b0976ea97b89e73195bfa97880ab25203ef55e))
* **deps:** bump actions/dependency-review-action from 4.7.1 to 4.7.2 ([ade020f](https://github.com/rknightion/meraki-dashboard-ha/commit/ade020f342e6e5284ad3dab924f74bfb8299b4a3))
* **deps:** bump astral-sh/setup-uv from 6.4.3 to 6.5.0 ([d04ec8b](https://github.com/rknightion/meraki-dashboard-ha/commit/d04ec8bfc936229a583223b94c68947cd934c2c9))
* **deps:** bump astral-sh/setup-uv from 6.4.3 to 6.5.0 ([c9cb0ef](https://github.com/rknightion/meraki-dashboard-ha/commit/c9cb0ef19ac62ed0860032099a1e71d11ea2c0b4))
* **deps:** bump astral-sh/setup-uv from 6.5.0 to 6.6.0 ([df3abea](https://github.com/rknightion/meraki-dashboard-ha/commit/df3abea06b01e1c5e0f3f2661133a2c08a64c9b1))
* **deps:** bump astral-sh/setup-uv from 6.5.0 to 6.6.0 ([2c39a24](https://github.com/rknightion/meraki-dashboard-ha/commit/2c39a24d8d0e6b6cf16b6417d6d6f8288ff77e2a))
* **deps:** bump codecov/codecov-action from 5.4.3 to 5.5.0 ([42fe343](https://github.com/rknightion/meraki-dashboard-ha/commit/42fe34336a650613c3335be604f42edb4cda9cad))
* **deps:** bump codecov/codecov-action from 5.4.3 to 5.5.0 ([7fcb027](https://github.com/rknightion/meraki-dashboard-ha/commit/7fcb027c575ba3ce522f3eb83d2cfad77a975089))
* **deps:** bump homeassistant-stubs from 2025.7.3 to 2025.8.0 ([32becaa](https://github.com/rknightion/meraki-dashboard-ha/commit/32becaa965ec41374969d132a7ab3b2270c82e2b))
* **deps:** bump homeassistant-stubs from 2025.7.3 to 2025.8.0 ([2379bc2](https://github.com/rknightion/meraki-dashboard-ha/commit/2379bc2abcbf5488444a502b95b5d64c2539ddd9))
* **deps:** bump homeassistant-stubs from 2025.8.0 to 2025.8.1 ([a891450](https://github.com/rknightion/meraki-dashboard-ha/commit/a891450c0e6647cfe026af521693ddc3601c3140))
* **deps:** bump homeassistant-stubs from 2025.8.0 to 2025.8.1 ([a46b9bc](https://github.com/rknightion/meraki-dashboard-ha/commit/a46b9bcf1d0978b9a1c37006049f3c66c4ae0295))
* **deps:** bump homeassistant-stubs from 2025.8.1 to 2025.8.2 ([e6845d9](https://github.com/rknightion/meraki-dashboard-ha/commit/e6845d91d836e07d47de711f6e198fd884a8b46c))
* **deps:** bump homeassistant-stubs from 2025.8.1 to 2025.8.2 ([c0665b0](https://github.com/rknightion/meraki-dashboard-ha/commit/c0665b0f34dee1dc2a2777be2d955d42b62652b5))
* **deps:** bump homeassistant-stubs from 2025.8.2 to 2025.8.3 ([4c2811a](https://github.com/rknightion/meraki-dashboard-ha/commit/4c2811adbd91cc2ecd6df506e1b4c0f90a9d2481))
* **deps:** bump homeassistant-stubs from 2025.8.2 to 2025.8.3 ([d35def3](https://github.com/rknightion/meraki-dashboard-ha/commit/d35def355a6e11bd59b02f4e49b3ed3717af0521))
* **deps:** bump mkdocs-material from 9.6.16 to 9.6.17 ([0a6c4fc](https://github.com/rknightion/meraki-dashboard-ha/commit/0a6c4fc7744880e07e19b3ae871afca2151ab731))
* **deps:** bump mkdocs-material from 9.6.16 to 9.6.17 ([26fb0e8](https://github.com/rknightion/meraki-dashboard-ha/commit/26fb0e8895516d257a713833c61748fa3d1a9b5d))
* **deps:** bump mkdocs-material from 9.6.17 to 9.6.18 ([6f69ae6](https://github.com/rknightion/meraki-dashboard-ha/commit/6f69ae651b2298de55cadf0a4358a6ff66bf1a3f))
* **deps:** bump mkdocs-material from 9.6.17 to 9.6.18 ([3e95716](https://github.com/rknightion/meraki-dashboard-ha/commit/3e95716840eddde537298a9eb59d5f18c0b8ca81))
* **deps:** bump ossf/scorecard-action from 2.4.0 to 2.4.2 ([68012e6](https://github.com/rknightion/meraki-dashboard-ha/commit/68012e6152aea1b323342b2f43395800705841d3))
* **deps:** bump ossf/scorecard-action from 2.4.0 to 2.4.2 ([395d056](https://github.com/rknightion/meraki-dashboard-ha/commit/395d056d48443010e912d8b61e3bf2ddd6a6bc4e))
* **deps:** bump pytest-homeassistant-custom-component ([d1e1791](https://github.com/rknightion/meraki-dashboard-ha/commit/d1e17913ce1bb827eb8ab7985f8706d74e5c1241))
* **deps:** bump pytest-homeassistant-custom-component from 0.13.263 to 0.13.266 ([1eb09f9](https://github.com/rknightion/meraki-dashboard-ha/commit/1eb09f92a4ba3bfdcd9772f8ce240f8a74142179))
* **deps:** bump ruff from 0.12.5 to 0.12.7 ([e9175d4](https://github.com/rknightion/meraki-dashboard-ha/commit/e9175d43889c679623ab851cdebc9b54781783d5))
* **deps:** bump ruff from 0.12.5 to 0.12.7 ([ee22490](https://github.com/rknightion/meraki-dashboard-ha/commit/ee2249085f884becc957e1a1e1982336772afe7c))
* **deps:** bump ruff from 0.12.7 to 0.12.8 ([f55d7a0](https://github.com/rknightion/meraki-dashboard-ha/commit/f55d7a081b4b10110f6f1587001b450ae3ed4dc7))
* **deps:** bump ruff from 0.12.7 to 0.12.8 ([60796d0](https://github.com/rknightion/meraki-dashboard-ha/commit/60796d057e49463d2ffd3b064da9495a136bdb6d))
* **deps:** bump ruff from 0.12.9 to 0.12.10 ([55fbfa4](https://github.com/rknightion/meraki-dashboard-ha/commit/55fbfa4adb88b1c4df8f9d1a79a782df5e353278))
* **deps:** bump ruff from 0.12.9 to 0.12.10 ([372d112](https://github.com/rknightion/meraki-dashboard-ha/commit/372d1122b409fc11d373195cbb1785465902d0c2))
* **deps:** bump zizmorcore/zizmor-action from 0.1.1 to 0.1.2 ([fc22186](https://github.com/rknightion/meraki-dashboard-ha/commit/fc22186be168a1d54c3f90a14d1c396f93c8fb74))
* **deps:** lock file maintenance ([9645394](https://github.com/rknightion/meraki-dashboard-ha/commit/9645394596fe51af2e52c60f692e7c5d4a63e44d))
* **deps:** lock file maintenance ([bde285b](https://github.com/rknightion/meraki-dashboard-ha/commit/bde285b628e0fe3b293bed45aea7542636135196))
* **deps:** lock file maintenance ([#104](https://github.com/rknightion/meraki-dashboard-ha/issues/104)) ([cfc04a5](https://github.com/rknightion/meraki-dashboard-ha/commit/cfc04a54c6adea4a4555f339e07f5e670e993488))
* **deps:** lock file maintenance ([#113](https://github.com/rknightion/meraki-dashboard-ha/issues/113)) ([ed52957](https://github.com/rknightion/meraki-dashboard-ha/commit/ed529575ce72d1d1c26ddc4cebd196de191171fa))
* **deps:** lock file maintenance ([#116](https://github.com/rknightion/meraki-dashboard-ha/issues/116)) ([476a173](https://github.com/rknightion/meraki-dashboard-ha/commit/476a173769c0e6e89aa3f511fe1c6fe8af90c1ec))
* **deps:** lock file maintenance ([#122](https://github.com/rknightion/meraki-dashboard-ha/issues/122)) ([a1e82cb](https://github.com/rknightion/meraki-dashboard-ha/commit/a1e82cbfa3e5f11d72e70b7efa9872adafed777f))
* **deps:** lock file maintenance ([#130](https://github.com/rknightion/meraki-dashboard-ha/issues/130)) ([030331e](https://github.com/rknightion/meraki-dashboard-ha/commit/030331e71fb041a4a12fcc904940d3aa2645d4a6))
* **deps:** lock file maintenance ([#142](https://github.com/rknightion/meraki-dashboard-ha/issues/142)) ([c059a47](https://github.com/rknightion/meraki-dashboard-ha/commit/c059a47256bea6e1a1de269763cedefe7485563b))
* **deps:** lock file maintenance ([#94](https://github.com/rknightion/meraki-dashboard-ha/issues/94)) ([e5d3f12](https://github.com/rknightion/meraki-dashboard-ha/commit/e5d3f12efc46f598982b6174288bc32f7c44117d))
* **deps:** pin dependencies ([#93](https://github.com/rknightion/meraki-dashboard-ha/issues/93)) ([74f882e](https://github.com/rknightion/meraki-dashboard-ha/commit/74f882eb1369f5a0cc8c2878c58b430e3e8239c0))
* **deps:** update actions/ai-inference action to v2.0.1 ([#95](https://github.com/rknightion/meraki-dashboard-ha/issues/95)) ([87eb4d5](https://github.com/rknightion/meraki-dashboard-ha/commit/87eb4d56215f8d07f8259c22371e73eeae0618b9))
* **deps:** update actions/dependency-review-action action to v4.7.3 ([#96](https://github.com/rknightion/meraki-dashboard-ha/issues/96)) ([351a508](https://github.com/rknightion/meraki-dashboard-ha/commit/351a5083067b22249e6b2c3564b3f7a23ba75896))
* **deps:** update actions/dependency-review-action action to v4.8.0 ([#121](https://github.com/rknightion/meraki-dashboard-ha/issues/121)) ([53816de](https://github.com/rknightion/meraki-dashboard-ha/commit/53816de24714b56c69c604867c5d2587230533b7))
* **deps:** update actions/dependency-review-action action to v4.8.1 ([#139](https://github.com/rknightion/meraki-dashboard-ha/issues/139)) ([faa74cb](https://github.com/rknightion/meraki-dashboard-ha/commit/faa74cbda349cd61b9da9869a59098d492a5eec4))
* **deps:** update actions/setup-python action to v6 ([#102](https://github.com/rknightion/meraki-dashboard-ha/issues/102)) ([cb8422c](https://github.com/rknightion/meraki-dashboard-ha/commit/cb8422cb9d97440aabd6aadccdd11fae3aa36c7d))
* **deps:** update actions/stale action to v10 ([#103](https://github.com/rknightion/meraki-dashboard-ha/issues/103)) ([97e549a](https://github.com/rknightion/meraki-dashboard-ha/commit/97e549a71d7a571680abb3d9eda55558912c55f1))
* **deps:** update actions/stale action to v10.1.0 ([#129](https://github.com/rknightion/meraki-dashboard-ha/issues/129)) ([04cc8b8](https://github.com/rknightion/meraki-dashboard-ha/commit/04cc8b89eb31754699143644aa9929559c75e4d6))
* **deps:** update actions/upload-artifact action to v5 ([24a3fdd](https://github.com/rknightion/meraki-dashboard-ha/commit/24a3fdd7eb6b7e91e2128f1aeb65d3b323e45994))
* **deps:** update actions/upload-artifact action to v5 ([1b4c9eb](https://github.com/rknightion/meraki-dashboard-ha/commit/1b4c9eb5145c1c5eeffd22fc2a80b4efe752ec73))
* **deps:** update astral-sh/setup-uv action to v6.6.1 ([#98](https://github.com/rknightion/meraki-dashboard-ha/issues/98)) ([ea8cf9d](https://github.com/rknightion/meraki-dashboard-ha/commit/ea8cf9df5bc5498e75786485169e0aebf5a36fd6))
* **deps:** update astral-sh/setup-uv action to v6.7.0 ([#112](https://github.com/rknightion/meraki-dashboard-ha/issues/112)) ([95e3f17](https://github.com/rknightion/meraki-dashboard-ha/commit/95e3f17dd2bf10756819880892b6873c0ba0fd39))
* **deps:** update astral-sh/setup-uv action to v6.8.0 ([#123](https://github.com/rknightion/meraki-dashboard-ha/issues/123)) ([35f2ca0](https://github.com/rknightion/meraki-dashboard-ha/commit/35f2ca0e2d234b53a300f785888b298f6f846307))
* **deps:** update astral-sh/setup-uv action to v7 ([#135](https://github.com/rknightion/meraki-dashboard-ha/issues/135)) ([d538ae6](https://github.com/rknightion/meraki-dashboard-ha/commit/d538ae6f04568bdbe3403afd6a7b4916b5f96d0f))
* **deps:** update astral-sh/setup-uv action to v7.1.0 ([#141](https://github.com/rknightion/meraki-dashboard-ha/issues/141)) ([05914bc](https://github.com/rknightion/meraki-dashboard-ha/commit/05914bcd53e79171c08594320b7f75eaecd0069a))
* **deps:** update astral-sh/setup-uv action to v7.1.2 ([e0e79c3](https://github.com/rknightion/meraki-dashboard-ha/commit/e0e79c35632e99bb98fd7901841aa669dcb761c9))
* **deps:** update astral-sh/setup-uv action to v7.1.2 ([82a77a1](https://github.com/rknightion/meraki-dashboard-ha/commit/82a77a132619479ed8c2daffb96cb4c8decde4ee))
* **deps:** update codecov/codecov-action action to v5.5.1 ([#99](https://github.com/rknightion/meraki-dashboard-ha/issues/99)) ([3e7ec1a](https://github.com/rknightion/meraki-dashboard-ha/commit/3e7ec1a4fa387e2384fb8725887beb1ec8f69b3e))
* **deps:** update dependency homeassistant-stubs to v2025.10.1 ([#126](https://github.com/rknightion/meraki-dashboard-ha/issues/126)) ([e1b8b89](https://github.com/rknightion/meraki-dashboard-ha/commit/e1b8b890e1dc270548dd56cd43a51dcc39d62c72))
* **deps:** update dependency homeassistant-stubs to v2025.10.2 ([#140](https://github.com/rknightion/meraki-dashboard-ha/issues/140)) ([b9513cd](https://github.com/rknightion/meraki-dashboard-ha/commit/b9513cdf9ac148d4bd781feaed4d485c31d79271))
* **deps:** update dependency homeassistant-stubs to v2025.10.3 ([70293a4](https://github.com/rknightion/meraki-dashboard-ha/commit/70293a41e911719ad2679097147ec83d473137a8))
* **deps:** update dependency homeassistant-stubs to v2025.11.0 ([c8feb18](https://github.com/rknightion/meraki-dashboard-ha/commit/c8feb1829203312e602141a49e314ff059d0a662))
* **deps:** update dependency homeassistant-stubs to v2025.11.0 ([f4a5e03](https://github.com/rknightion/meraki-dashboard-ha/commit/f4a5e031bfd7d457c25371f5e3d054fcbbf35c65))
* **deps:** update dependency homeassistant-stubs to v2025.9.1 ([#100](https://github.com/rknightion/meraki-dashboard-ha/issues/100)) ([cf3fe02](https://github.com/rknightion/meraki-dashboard-ha/commit/cf3fe0251732d08feef15872852f9c26573f4803))
* **deps:** update dependency homeassistant-stubs to v2025.9.3 ([#111](https://github.com/rknightion/meraki-dashboard-ha/issues/111)) ([2a310b3](https://github.com/rknightion/meraki-dashboard-ha/commit/2a310b3b1672e1ef99dee6ff81b3a557d9742fa3))
* **deps:** update dependency homeassistant-stubs to v2025.9.4 ([#115](https://github.com/rknightion/meraki-dashboard-ha/issues/115)) ([ed6db0d](https://github.com/rknightion/meraki-dashboard-ha/commit/ed6db0d13bacc5521e8903f97b33a1a1c36d1b3b))
* **deps:** update dependency http_parser.rb to "~&gt; 0.8.0" ([62b9fa7](https://github.com/rknightion/meraki-dashboard-ha/commit/62b9fa759a63577c2375bdf09574bc4e471a689f))
* **deps:** update dependency http_parser.rb to "~&gt; 0.8.0" ([1a07dfd](https://github.com/rknightion/meraki-dashboard-ha/commit/1a07dfdf60f06a220e99f3671dd60866b081430c))
* **deps:** update dependency wdm to "~&gt; 0.2.0" ([8977150](https://github.com/rknightion/meraki-dashboard-ha/commit/8977150b67c6f5327ccd00430b47d03f458a2956))
* **deps:** update dependency wdm to "~&gt; 0.2.0" ([c6435a5](https://github.com/rknightion/meraki-dashboard-ha/commit/c6435a52cc2ad507c85c0127d71f942964c1cbde))
* **deps:** update dependency wrangler to v4 ([334c7cc](https://github.com/rknightion/meraki-dashboard-ha/commit/334c7cc652065896eb99a220911a09f674da1e2b))
* **deps:** update development dependencies and format code ([87f66fb](https://github.com/rknightion/meraki-dashboard-ha/commit/87f66fbf45415bf23afbe5d6998a18ea91ef315c))
* **deps:** update github/codeql-action action to v3.29.11 ([#81](https://github.com/rknightion/meraki-dashboard-ha/issues/81)) ([a920082](https://github.com/rknightion/meraki-dashboard-ha/commit/a92008270ad48359fd2c67d6e98137b26564f7a3))
* **deps:** update github/codeql-action action to v3.29.8 ([ca63404](https://github.com/rknightion/meraki-dashboard-ha/commit/ca6340406a6de36f635a8b45f38ea8290e567b4a))
* **deps:** update github/codeql-action action to v3.29.8 ([df05769](https://github.com/rknightion/meraki-dashboard-ha/commit/df057692bd7aeee3a36594c3383189c2de06f96c))
* **deps:** update github/codeql-action action to v3.29.9 ([2b37db0](https://github.com/rknightion/meraki-dashboard-ha/commit/2b37db02edc7504f2b2d60f88627b4613cf7b231))
* **deps:** update github/codeql-action action to v3.30.1 ([#101](https://github.com/rknightion/meraki-dashboard-ha/issues/101)) ([2353fd6](https://github.com/rknightion/meraki-dashboard-ha/commit/2353fd68b8e7e59c0c2a40c25047d5c578e49f9b))
* **deps:** update github/codeql-action action to v3.30.2 ([#106](https://github.com/rknightion/meraki-dashboard-ha/issues/106)) ([ca9576b](https://github.com/rknightion/meraki-dashboard-ha/commit/ca9576b34e5426283a615af41e98fab8334e24eb))
* **deps:** update github/codeql-action action to v3.30.3 ([#109](https://github.com/rknightion/meraki-dashboard-ha/issues/109)) ([3dc4602](https://github.com/rknightion/meraki-dashboard-ha/commit/3dc46020f9dedbd60f1e79ed0f7853d991f062ad))
* **deps:** update github/codeql-action action to v3.30.4 ([#118](https://github.com/rknightion/meraki-dashboard-ha/issues/118)) ([07ed54c](https://github.com/rknightion/meraki-dashboard-ha/commit/07ed54c9df0f63eda76fa13fb344695caf6ccfc0))
* **deps:** update github/codeql-action action to v3.30.5 ([#120](https://github.com/rknightion/meraki-dashboard-ha/issues/120)) ([d902fc0](https://github.com/rknightion/meraki-dashboard-ha/commit/d902fc0dd617258fc65ac3f6bb541aea33e94a7e))
* **deps:** update github/codeql-action action to v3.30.6 ([#128](https://github.com/rknightion/meraki-dashboard-ha/issues/128)) ([fdb636d](https://github.com/rknightion/meraki-dashboard-ha/commit/fdb636dc67272399db21a9d9b7e5e0534e897ed0))
* **deps:** update github/codeql-action action to v3.30.7 ([#134](https://github.com/rknightion/meraki-dashboard-ha/issues/134)) ([e9e1be4](https://github.com/rknightion/meraki-dashboard-ha/commit/e9e1be4fa1180bc202e7db76a94f8a3b4f936493))
* **deps:** update github/codeql-action action to v4 ([#136](https://github.com/rknightion/meraki-dashboard-ha/issues/136)) ([3b0209d](https://github.com/rknightion/meraki-dashboard-ha/commit/3b0209d6e13480623dcbd06e25f0c23c1692633a))
* **deps:** update github/codeql-action action to v4.30.8 ([#138](https://github.com/rknightion/meraki-dashboard-ha/issues/138)) ([3bbd594](https://github.com/rknightion/meraki-dashboard-ha/commit/3bbd594b1070f4cfc98ba4c19a3d6b4c503a3604))
* **deps:** update github/codeql-action action to v4.30.9 ([43be414](https://github.com/rknightion/meraki-dashboard-ha/commit/43be41446ba9d737ba59fbdec003816f68a08d07))
* **deps:** update github/codeql-action action to v4.30.9 ([3860490](https://github.com/rknightion/meraki-dashboard-ha/commit/3860490d45be0465d3da00c74cf6de4ba37f64cd))
* **deps:** update github/codeql-action action to v4.31.2 ([#152](https://github.com/rknightion/meraki-dashboard-ha/issues/152)) ([694c7d8](https://github.com/rknightion/meraki-dashboard-ha/commit/694c7d808720df4f9f10624a2f045d510b9632ca))
* **deps:** update github/codeql-action digest to 0499de3 ([#151](https://github.com/rknightion/meraki-dashboard-ha/issues/151)) ([f93d596](https://github.com/rknightion/meraki-dashboard-ha/commit/f93d59609665fa9c8bfafc65e96dae40106a52bc))
* **deps:** update github/codeql-action digest to 16140ae ([#145](https://github.com/rknightion/meraki-dashboard-ha/issues/145)) ([121f936](https://github.com/rknightion/meraki-dashboard-ha/commit/121f936ec577cf37ca95a1ce785251b67234499c))
* **deps:** update github/codeql-action digest to 192325c ([#108](https://github.com/rknightion/meraki-dashboard-ha/issues/108)) ([151b383](https://github.com/rknightion/meraki-dashboard-ha/commit/151b3833ebbf7b7d61a0137eb9ecc5325aea4156))
* **deps:** update github/codeql-action digest to 303c0ae ([#117](https://github.com/rknightion/meraki-dashboard-ha/issues/117)) ([7a64d5b](https://github.com/rknightion/meraki-dashboard-ha/commit/7a64d5b8b9921038aa32d8b7cbf480e12b2b94e5))
* **deps:** update github/codeql-action digest to 3599b3b ([#119](https://github.com/rknightion/meraki-dashboard-ha/issues/119)) ([abd45c0](https://github.com/rknightion/meraki-dashboard-ha/commit/abd45c027ffa0a1ae0845f85a9c6ba741e830ba5))
* **deps:** update github/codeql-action digest to 64d10c1 ([#127](https://github.com/rknightion/meraki-dashboard-ha/issues/127)) ([22aa593](https://github.com/rknightion/meraki-dashboard-ha/commit/22aa593d09fb9d9659c824dde5e7fb7348323858))
* **deps:** update github/codeql-action digest to a8d1ac4 ([#133](https://github.com/rknightion/meraki-dashboard-ha/issues/133)) ([7026902](https://github.com/rknightion/meraki-dashboard-ha/commit/70269024f3ad2a476462ef260a0fccb3fe31b17c))
* **deps:** update github/codeql-action digest to d3678e2 ([#105](https://github.com/rknightion/meraki-dashboard-ha/issues/105)) ([89eabd3](https://github.com/rknightion/meraki-dashboard-ha/commit/89eabd332e99b9402168b23873cc04e025186c4f))
* **deps:** update github/codeql-action digest to f1f6e5f ([#97](https://github.com/rknightion/meraki-dashboard-ha/issues/97)) ([217b5ad](https://github.com/rknightion/meraki-dashboard-ha/commit/217b5ad0bb8dd2079afb3a485c117f41a34c3e90))
* **deps:** update github/codeql-action digest to f443b60 ([#137](https://github.com/rknightion/meraki-dashboard-ha/issues/137)) ([61ad7ac](https://github.com/rknightion/meraki-dashboard-ha/commit/61ad7ac41e3d119e82aee00520043265d97db901))
* **deps:** update googleapis/release-please-action action to v4.4.0 ([#160](https://github.com/rknightion/meraki-dashboard-ha/issues/160)) ([d30e330](https://github.com/rknightion/meraki-dashboard-ha/commit/d30e330edad76387b41793f5f30668cf5ff503e8))
* **deps:** update home-assistant/actions digest to 342664e ([#110](https://github.com/rknightion/meraki-dashboard-ha/issues/110)) ([9ac1dae](https://github.com/rknightion/meraki-dashboard-ha/commit/9ac1daea4d411c211093e5c9751537c252184385))
* **deps:** update home-assistant/actions digest to 72e1db9 ([#80](https://github.com/rknightion/meraki-dashboard-ha/issues/80)) ([4300718](https://github.com/rknightion/meraki-dashboard-ha/commit/4300718280d49e9eb6476b498baa67e7d5cf306e))
* **deps:** update home-assistant/actions digest to 8ca6e13 ([#155](https://github.com/rknightion/meraki-dashboard-ha/issues/155)) ([e263b81](https://github.com/rknightion/meraki-dashboard-ha/commit/e263b81dbce49571801a08bb8167f3056282b643))
* **deps:** update home-assistant/actions digest to e5c9826 ([#131](https://github.com/rknightion/meraki-dashboard-ha/issues/131)) ([c438dc3](https://github.com/rknightion/meraki-dashboard-ha/commit/c438dc3ded2cddeaefecbaccd5bdbe74f1788816))
* **deps:** update mcr.microsoft.com/devcontainers/python docker tag to v3.14 ([64be4d5](https://github.com/rknightion/meraki-dashboard-ha/commit/64be4d532f3935384cd1cd7066a340d467f01e17))
* **deps:** update mcr.microsoft.com/devcontainers/python docker tag to v3.14 ([a696e5b](https://github.com/rknightion/meraki-dashboard-ha/commit/a696e5bcfc9a2464dfa3a124d57fc9cb68fa8be1))
* **deps:** update ossf/scorecard-action action to v2.4.3 ([#124](https://github.com/rknightion/meraki-dashboard-ha/issues/124)) ([4d52988](https://github.com/rknightion/meraki-dashboard-ha/commit/4d529881063146a51567c62ef15f7334405059a9))
* **deps:** update peter-evans/repository-dispatch action to v4 ([#125](https://github.com/rknightion/meraki-dashboard-ha/issues/125)) ([09f3d01](https://github.com/rknightion/meraki-dashboard-ha/commit/09f3d0130adf598726be963370975c198245e5ca))
* **deps:** update step-security/harden-runner action to v2.13.1 ([#107](https://github.com/rknightion/meraki-dashboard-ha/issues/107)) ([296e4e0](https://github.com/rknightion/meraki-dashboard-ha/commit/296e4e0bf0a1de6fe26d230092318d6e3891bd99))
* **deps:** update step-security/harden-runner action to v2.13.2 ([1bf5877](https://github.com/rknightion/meraki-dashboard-ha/commit/1bf5877ec59df2c48f6f43b41a92cfb76c6f8376))
* **deps:** update step-security/harden-runner action to v2.13.2 ([f9f32aa](https://github.com/rknightion/meraki-dashboard-ha/commit/f9f32aa3044151fefd444f9cb4fda63a8c0f01f1))
* **deps:** update zizmorcore/zizmor-action action to v0.1.2 ([26072b6](https://github.com/rknightion/meraki-dashboard-ha/commit/26072b621f417dd239c7f29ac4194d090ec08e10))
* **deps:** update zizmorcore/zizmor-action action to v0.2.0 ([#114](https://github.com/rknightion/meraki-dashboard-ha/issues/114)) ([a6b5e06](https://github.com/rknightion/meraki-dashboard-ha/commit/a6b5e06fb183cf834c438a1858d5bce0e957f747))
* email ([7c265e4](https://github.com/rknightion/meraki-dashboard-ha/commit/7c265e4b2a1548aa66ae47bf9bdc30a7c48a9665))
* enhance CI workflow and improve test coverage ([fa972a8](https://github.com/rknightion/meraki-dashboard-ha/commit/fa972a85717343593660b4684de21ec14e921fb4))
* enhance configuration migration and validation ([adff896](https://github.com/rknightion/meraki-dashboard-ha/commit/adff896b308dfe8fc52d5bcd99da9652e25ae983))
* enhance development environment support ([c823bdd](https://github.com/rknightion/meraki-dashboard-ha/commit/c823bdd37597719dd13904dc78010070b1523849))
* fix ([6cc5804](https://github.com/rknightion/meraki-dashboard-ha/commit/6cc58040dadadfb3f1059b725633587105210c0b))
* fix ci ([56c146f](https://github.com/rknightion/meraki-dashboard-ha/commit/56c146f1a2a085c6f29a7ac35852f9fd8ac4e3f4))
* improve type safety and code quality ([fd2602e](https://github.com/rknightion/meraki-dashboard-ha/commit/fd2602ead2f3697132640ca06d530290c6bb52e4))
* **main:** release 0.10.0 ([f6f37c5](https://github.com/rknightion/meraki-dashboard-ha/commit/f6f37c571ad3c307392d7d693fd815280cc86d0a))
* **main:** release 0.10.0 ([37326c7](https://github.com/rknightion/meraki-dashboard-ha/commit/37326c7143ef0c49af191105fe32f40132ad0d36))
* **main:** release 0.11.0 ([cdaa0fb](https://github.com/rknightion/meraki-dashboard-ha/commit/cdaa0fb3312963c2dfcd9fab024a7092a4a3bf02))
* **main:** release 0.11.0 ([d6f0f11](https://github.com/rknightion/meraki-dashboard-ha/commit/d6f0f11c389788454232a939e95769c373925052))
* **main:** release 0.12.0 ([#20](https://github.com/rknightion/meraki-dashboard-ha/issues/20)) ([3853329](https://github.com/rknightion/meraki-dashboard-ha/commit/3853329c804cc4e79ca8d6d643d34596d3ef9020))
* **main:** release 0.12.1 ([#21](https://github.com/rknightion/meraki-dashboard-ha/issues/21)) ([8b9311b](https://github.com/rknightion/meraki-dashboard-ha/commit/8b9311bb2cb2b41c408632e286a41c9a3792eda9))
* **main:** release 0.12.2 ([#22](https://github.com/rknightion/meraki-dashboard-ha/issues/22)) ([27db1a0](https://github.com/rknightion/meraki-dashboard-ha/commit/27db1a0dcff9a6e4e45cd1b6de644aa8c2cc8645))
* **main:** release 0.12.3 ([#23](https://github.com/rknightion/meraki-dashboard-ha/issues/23)) ([29bf0eb](https://github.com/rknightion/meraki-dashboard-ha/commit/29bf0eb7a605f78d8dae9279d935f156cdcbe8bf))
* **main:** release 0.13.0 ([#24](https://github.com/rknightion/meraki-dashboard-ha/issues/24)) ([03ba4a1](https://github.com/rknightion/meraki-dashboard-ha/commit/03ba4a1295ee74d466456be0fb66f2c172c1263a))
* **main:** release 0.4.0 ([e50aaa5](https://github.com/rknightion/meraki-dashboard-ha/commit/e50aaa50ad057cd1b03a4e0786236f7ae33005b7))
* **main:** release 0.4.0 ([2d6ffd6](https://github.com/rknightion/meraki-dashboard-ha/commit/2d6ffd660e255c768d4ed9f76f0c0f86bb6891d3))
* **main:** release 0.5.0 ([e2ffbbb](https://github.com/rknightion/meraki-dashboard-ha/commit/e2ffbbbe4e13ed644922ee4422b5fa128c008543))
* **main:** release 0.5.0 ([ca1e073](https://github.com/rknightion/meraki-dashboard-ha/commit/ca1e07329cc8ad609fb0d5fd76e17c04c6fcf336))
* **main:** release 0.6.0 ([21d3617](https://github.com/rknightion/meraki-dashboard-ha/commit/21d361704e10832c68d5ee18d655076951542a77))
* **main:** release 0.6.0 ([8174d3a](https://github.com/rknightion/meraki-dashboard-ha/commit/8174d3ab5caa41fc05f23978e6e5c6807b5fa8a0))
* **main:** release 0.7.0 ([72b250d](https://github.com/rknightion/meraki-dashboard-ha/commit/72b250d34e2f6735cd1ba7c276467a6fce82dd5d))
* **main:** release 0.7.0 ([9d8f445](https://github.com/rknightion/meraki-dashboard-ha/commit/9d8f4451d360481c74dc474b987bc7b7773ef4d9))
* **main:** release 0.8.0 ([27ba9f1](https://github.com/rknightion/meraki-dashboard-ha/commit/27ba9f106763dd1aebfd780078e0528dfcac8e0e))
* **main:** release 0.8.0 ([50f8ade](https://github.com/rknightion/meraki-dashboard-ha/commit/50f8ade23d42bb8c7e136cefe95fd52ca8199aa7))
* **main:** release 0.9.0 ([618490a](https://github.com/rknightion/meraki-dashboard-ha/commit/618490a6e0dc30b0d1e88c597477cac7ebc57b83))
* **main:** release 0.9.0 ([12c7b98](https://github.com/rknightion/meraki-dashboard-ha/commit/12c7b9838650f4428393d33ea08a962579ab8e3c))
* **main:** release 0.9.1 ([cc5b4c3](https://github.com/rknightion/meraki-dashboard-ha/commit/cc5b4c3a57805ca73df79fee853ee31fa7e1f92e))
* **main:** release 0.9.1 ([b729224](https://github.com/rknightion/meraki-dashboard-ha/commit/b7292242ca23b1046931949f69fe71a067a9692f))
* **main:** release 0.9.2 ([789a640](https://github.com/rknightion/meraki-dashboard-ha/commit/789a64043cd07f05cca427febd62c5679501f722))
* **main:** release 0.9.2 ([391c531](https://github.com/rknightion/meraki-dashboard-ha/commit/391c531e4cfa648a6ca67abf2cfbdd81d06850f8))
* **main:** release 0.9.3 ([c5c22f9](https://github.com/rknightion/meraki-dashboard-ha/commit/c5c22f9eaab91962f4a52599c8c236769b131555))
* **main:** release 0.9.3 ([abc516a](https://github.com/rknightion/meraki-dashboard-ha/commit/abc516aaddb712dd0da6a3ca0a6a390d6d543631))
* **main:** release 0.9.4 ([7d1872c](https://github.com/rknightion/meraki-dashboard-ha/commit/7d1872ca13c03382cc2edfdebdc8457a9b7a6309))
* **main:** release 0.9.4 ([bd1f6ac](https://github.com/rknightion/meraki-dashboard-ha/commit/bd1f6acbe07d04a2f84c664883d51f3a9efa0f62))
* **main:** release meraki-dashboard-ha 0.13.0 ([#25](https://github.com/rknightion/meraki-dashboard-ha/issues/25)) ([37725cc](https://github.com/rknightion/meraki-dashboard-ha/commit/37725cc38b4b1282dee4f91ac9cc37a1ae3cceaa))
* **main:** release meraki-dashboard-ha 0.14.0 ([#26](https://github.com/rknightion/meraki-dashboard-ha/issues/26)) ([ede09e3](https://github.com/rknightion/meraki-dashboard-ha/commit/ede09e3040ebc310f539605c4ea3714a70caa891))
* **main:** release meraki-dashboard-ha 0.15.0 ([#27](https://github.com/rknightion/meraki-dashboard-ha/issues/27)) ([ecebf6e](https://github.com/rknightion/meraki-dashboard-ha/commit/ecebf6e2e8761c1d9a8de77f1151596f42d03b47))
* **main:** release meraki-dashboard-ha 0.16.0 ([#28](https://github.com/rknightion/meraki-dashboard-ha/issues/28)) ([a76a6e6](https://github.com/rknightion/meraki-dashboard-ha/commit/a76a6e6c319684d4b194b3467ef48d63825c16a4))
* **main:** release meraki-dashboard-ha 0.17.0 ([#29](https://github.com/rknightion/meraki-dashboard-ha/issues/29)) ([97b3110](https://github.com/rknightion/meraki-dashboard-ha/commit/97b3110f338949d08b28f8df45974a5a8f091837))
* **main:** release meraki-dashboard-ha 0.18.0 ([#30](https://github.com/rknightion/meraki-dashboard-ha/issues/30)) ([560552b](https://github.com/rknightion/meraki-dashboard-ha/commit/560552b4af68300d65f1fa4cae6e6097aeea5cd1))
* **main:** release meraki-dashboard-ha 0.19.0 ([#31](https://github.com/rknightion/meraki-dashboard-ha/issues/31)) ([c59a365](https://github.com/rknightion/meraki-dashboard-ha/commit/c59a3657e16b57802bcac193342b0749e2d5f364))
* **main:** release meraki-dashboard-ha 0.20.0 ([#32](https://github.com/rknightion/meraki-dashboard-ha/issues/32)) ([47fc9c3](https://github.com/rknightion/meraki-dashboard-ha/commit/47fc9c322712f55ded9e5a31a9f43e3541a5f9e3))
* **main:** release meraki-dashboard-ha 0.21.0 ([#33](https://github.com/rknightion/meraki-dashboard-ha/issues/33)) ([8085e4c](https://github.com/rknightion/meraki-dashboard-ha/commit/8085e4c505ab1fac0db9b5c4cd4184a7f0119afe))
* **main:** release meraki-dashboard-ha 0.22.0 ([71c6b58](https://github.com/rknightion/meraki-dashboard-ha/commit/71c6b589e8ab451094e5bfdeecf2b9b565532e4c))
* **main:** release meraki-dashboard-ha 0.22.0 ([e545a60](https://github.com/rknightion/meraki-dashboard-ha/commit/e545a605cc6ebe1ebfa22f0a5d165ca5ab0ad1ee))
* **main:** release meraki-dashboard-ha 0.23.0 ([#35](https://github.com/rknightion/meraki-dashboard-ha/issues/35)) ([615dc8e](https://github.com/rknightion/meraki-dashboard-ha/commit/615dc8e3e58b82caf7dc040192e588bbaefe0b47))
* Refactors Meraki integration for improved type safety ([2a63ce0](https://github.com/rknightion/meraki-dashboard-ha/commit/2a63ce06e0f2787ed58eb84d34bfc1c86626b301)), closes [#123](https://github.com/rknightion/meraki-dashboard-ha/issues/123)
* reintroduce comprehensive test suite and CI workflow ([648714d](https://github.com/rknightion/meraki-dashboard-ha/commit/648714db4a1f53e3e27e69a456386b848e709624))
* release 0.31.0 ([b07c507](https://github.com/rknightion/meraki-dashboard-ha/commit/b07c507ddd660d075c1dfeb59ee39a2ac766eee6))
* release 0.31.0 ([30d064b](https://github.com/rknightion/meraki-dashboard-ha/commit/30d064b1ff44f254ced834729b8f3d4f297b887b))
* **release:** remove pull request header from config ([5595d0c](https://github.com/rknightion/meraki-dashboard-ha/commit/5595d0cb3ba8252ffdba023f1c4c8262c9f6a35a))
* remove deprecated guidelines and rules files ([55db31b](https://github.com/rknightion/meraki-dashboard-ha/commit/55db31b2c3e2f8608c42f0fcd6750aa40aeef737))
* remove node_modules from search exclusion ([d837613](https://github.com/rknightion/meraki-dashboard-ha/commit/d8376131b3743d6df59b31f26df979037c31ef60))
* remove redundant pre-commit hooks ([1d92d86](https://github.com/rknightion/meraki-dashboard-ha/commit/1d92d8683f3edc4e32f70bfe356c07865b598cf3))
* replace custom release workflow with release-please ([e40a2b9](https://github.com/rknightion/meraki-dashboard-ha/commit/e40a2b94a3f5fc51639251813a22e3fa1562dbff))
* replace custom release workflow with release-please ([9c2e808](https://github.com/rknightion/meraki-dashboard-ha/commit/9c2e808be48acb24802eaeeeefacad15f8a15f3f))
* simplify workflow permissions ([f6a5551](https://github.com/rknightion/meraki-dashboard-ha/commit/f6a5551c9ec4204de8ca2e72f3ec326c85e99f91))
* update gitignore to track VS Code defaults while ignoring user settings ([4b02b62](https://github.com/rknightion/meraki-dashboard-ha/commit/4b02b62b1bae7805027422fc3e6585ba621b58f7))
* update permissions in workflows ([862cfee](https://github.com/rknightion/meraki-dashboard-ha/commit/862cfeea570bc0d641677b0b63884ad1ca8be2a3))
* update project dependencies to latest versions ([e19a9e1](https://github.com/rknightion/meraki-dashboard-ha/commit/e19a9e15bf09ac4af7a6e62eafb0b5d21e3fc0b1))
* update project name and domain pattern ([5a69c0a](https://github.com/rknightion/meraki-dashboard-ha/commit/5a69c0a535f366a64c882ab1ec347f37fe7b4c1d))
* update release-please configuration ([bbc212c](https://github.com/rknightion/meraki-dashboard-ha/commit/bbc212c19e06324213009597c9b1044aecfdad50))
* update ruff pre-commit hook to v0.14.4 ([ac98af7](https://github.com/rknightion/meraki-dashboard-ha/commit/ac98af7b8fde5ebb9068785ccfdab9ba8f344523))
* update ruff version and enhance config flow options ([2e0d1f1](https://github.com/rknightion/meraki-dashboard-ha/commit/2e0d1f15a1b5d148686b2950f69b2bf779024e55))
* update version to 0.23.5 and sync docs changelog ([d4047d7](https://github.com/rknightion/meraki-dashboard-ha/commit/d4047d7533bb09606428588e7aaca46ca0f26276))
* update version to 0.23.6 and sync docs changelog ([8f0415a](https://github.com/rknightion/meraki-dashboard-ha/commit/8f0415a014553ce233546a5b7e773d582b8f9e17))
* update version to 0.23.7 and sync docs changelog ([0fc234f](https://github.com/rknightion/meraki-dashboard-ha/commit/0fc234fa7e86d04db32192bd6706dc6677b95ee0))
* update version to 0.24.0 and sync docs changelog ([10b2b71](https://github.com/rknightion/meraki-dashboard-ha/commit/10b2b7131db1974b7af3581f33af6212376b6662))
* update version to 0.24.1 and sync docs changelog ([1b504d2](https://github.com/rknightion/meraki-dashboard-ha/commit/1b504d2b1bb52749d4c89d729f52237bb6ec37e3))
* update version to 0.24.10 and sync changelog ([a466460](https://github.com/rknightion/meraki-dashboard-ha/commit/a4664605c026ef94a91e475e3ae0b6d220059242))
* update version to 0.24.11 and sync changelog ([080f98f](https://github.com/rknightion/meraki-dashboard-ha/commit/080f98f0c762516b4b78afc4ed8dad38bb3db260))
* update version to 0.24.12 and sync changelog ([904f854](https://github.com/rknightion/meraki-dashboard-ha/commit/904f8542c16d3a96fb73f81b501c681a8971af3d))
* update version to 0.24.13 and sync changelog ([23b0318](https://github.com/rknightion/meraki-dashboard-ha/commit/23b0318ca1b5c74e8770e4ee73f697fdc8307a2d))
* update version to 0.24.14 and sync changelog ([d4d179e](https://github.com/rknightion/meraki-dashboard-ha/commit/d4d179e48c30dd33fd5d37b8226a5926bfa66094))
* update version to 0.24.15 and sync changelog ([bc3544c](https://github.com/rknightion/meraki-dashboard-ha/commit/bc3544c408e673253ba9c4b89a1f5284e2693e2c))
* update version to 0.24.16 and sync changelog ([bc80ee1](https://github.com/rknightion/meraki-dashboard-ha/commit/bc80ee17f773faf11c32383d2dbe596a56a37190))
* update version to 0.24.17 and sync changelog ([915838c](https://github.com/rknightion/meraki-dashboard-ha/commit/915838cb7e6b9c78e2e9c801fe7e0718038e328d))
* update version to 0.24.18 and sync changelog ([1c8fe8e](https://github.com/rknightion/meraki-dashboard-ha/commit/1c8fe8eeef8f93a47eb9505960e435c28cc17b16))
* update version to 0.24.19 and sync changelog ([8fb9eeb](https://github.com/rknightion/meraki-dashboard-ha/commit/8fb9eeb61db8d0e2fd490c31634dc500a4875af6))
* update version to 0.24.2 and sync docs changelog ([e513953](https://github.com/rknightion/meraki-dashboard-ha/commit/e5139537079f95b5906fa63df8c40a2c8cf6d24d))
* update version to 0.24.20 and sync changelog ([aeed62a](https://github.com/rknightion/meraki-dashboard-ha/commit/aeed62aa697913c30a33aaaeeb308c43fd5e5428))
* update version to 0.24.21 and sync changelog ([86f0ca8](https://github.com/rknightion/meraki-dashboard-ha/commit/86f0ca850b038c3534b297699b7281077bb1795d))
* update version to 0.24.22 and sync changelog ([8a27a55](https://github.com/rknightion/meraki-dashboard-ha/commit/8a27a55608aeb276a301542e610a6cb9901603c2))
* update version to 0.24.23 and sync changelog ([c717106](https://github.com/rknightion/meraki-dashboard-ha/commit/c7171062cac50dea54a6d8556f4f714a191f71df))
* update version to 0.24.24 and sync changelog ([e4d5ac4](https://github.com/rknightion/meraki-dashboard-ha/commit/e4d5ac4a8c993aa56f5886391f5e35f35da19252))
* update version to 0.24.28 and sync changelog ([83aebf4](https://github.com/rknightion/meraki-dashboard-ha/commit/83aebf4bace3ef6ad6779f89a7225839425ace2f))
* update version to 0.24.29 and sync changelog ([354cc77](https://github.com/rknightion/meraki-dashboard-ha/commit/354cc770c51cc856bc110018fbe95f8ef9e7bf26))
* update version to 0.24.3 and sync docs changelog ([d97b3a0](https://github.com/rknightion/meraki-dashboard-ha/commit/d97b3a008c7d72df731acd1613b943363e245f23))
* update version to 0.24.30 and sync changelog ([0a43c48](https://github.com/rknightion/meraki-dashboard-ha/commit/0a43c486c2283e53f91b2b175be2740929a580a7))
* update version to 0.24.4 and sync docs changelog ([859fd9e](https://github.com/rknightion/meraki-dashboard-ha/commit/859fd9ef234846f8ce803f3beead6b47448e5f8e))
* update version to 0.24.6 and sync changelog ([04bd1a2](https://github.com/rknightion/meraki-dashboard-ha/commit/04bd1a27d1918d4f2ef6acae51beba380bc4a6fe))
* update version to 0.24.8 and sync changelog ([0ee73e4](https://github.com/rknightion/meraki-dashboard-ha/commit/0ee73e4d302500e1aec278d5c22491b98663c591))
* update version to 0.24.9 and sync changelog ([8a46870](https://github.com/rknightion/meraki-dashboard-ha/commit/8a468704b6a397a6f262e8ba6fd6f482104e3931))
* update version to 0.25.0 and sync changelog ([b648ec1](https://github.com/rknightion/meraki-dashboard-ha/commit/b648ec169b672e49b6a51439d06cfd30e36a7590))
* update version to 0.25.1 and sync changelog ([b81b39d](https://github.com/rknightion/meraki-dashboard-ha/commit/b81b39d8669e391aa654e5a514026a178974b301))
* update version to 0.25.4 and sync changelog ([567c1ee](https://github.com/rknightion/meraki-dashboard-ha/commit/567c1ee2645e3ca0f7d6111fbde262c3bfafeeeb))
* update version to 0.25.5 and sync changelog ([d91cd42](https://github.com/rknightion/meraki-dashboard-ha/commit/d91cd42729832920baf7dc872689863381744189))
* update version to 0.25.6 and sync changelog ([a1fadef](https://github.com/rknightion/meraki-dashboard-ha/commit/a1fadef8d479e56e2b1b3e0e8b0e419038388916))
* update version to 0.26.0 and sync changelog ([94aca6b](https://github.com/rknightion/meraki-dashboard-ha/commit/94aca6bf81ea81cb6495d6f3e8d936ec80d8f75f))
* update version to 0.27.0 and sync changelog ([ed06e06](https://github.com/rknightion/meraki-dashboard-ha/commit/ed06e067c085ee039f052dcaade06cb4bc41cd8e))
* update version to 0.27.1 and sync changelog ([ef1cb60](https://github.com/rknightion/meraki-dashboard-ha/commit/ef1cb60cbf10e562cb572fdcf22c3f9763f10f65))
* update version to 0.27.2 and sync changelog ([93ed58b](https://github.com/rknightion/meraki-dashboard-ha/commit/93ed58b2b70c2d9045c95adcfec2d92b0371c727))
* update version to 0.28.0 and sync changelog ([80ecd47](https://github.com/rknightion/meraki-dashboard-ha/commit/80ecd4716f730810dd8b61552fb4dde7ef3f1337))
* update version to 0.28.1 and sync changelog ([655a4de](https://github.com/rknightion/meraki-dashboard-ha/commit/655a4de08bf7a4956c0bf831614d32c480d417af))
* update version to 0.28.2 and sync changelog ([924f5c2](https://github.com/rknightion/meraki-dashboard-ha/commit/924f5c2db4d56ddc6de1e8a8171827f97ea5e51b))
* update version to 0.30.0 and sync changelog ([293344b](https://github.com/rknightion/meraki-dashboard-ha/commit/293344bde63e8202746696444605d929cdd20a3f))
* update zizmor hook to v1.10.0 ([418855d](https://github.com/rknightion/meraki-dashboard-ha/commit/418855d2e79712619082fa40d3f091a9d60c3245))
* Updates pre-commit hooks ([c880baa](https://github.com/rknightion/meraki-dashboard-ha/commit/c880baa113082d81ff5f18e64d334ca06d5cfa10))


### Code Refactoring

* **config_flow:** move domain to class level for registration ([5028305](https://github.com/rknightion/meraki-dashboard-ha/commit/50283056888e41f5f3d6238cff358220163201a0))
* **config:** improve options flow UI and add API key update capability ([61d8650](https://github.com/rknightion/meraki-dashboard-ha/commit/61d86504feea0242c1c280f4526bfa1478187f6c))
* enhance error handling and refactor energy sensor logic ([ea69143](https://github.com/rknightion/meraki-dashboard-ha/commit/ea691435f852b50fe165d7afb77aa9fa604ca586))
* enhance hub option processing and precision settings ([3a913da](https://github.com/rknightion/meraki-dashboard-ha/commit/3a913da3e3dff384b4906449b233781e0b71f304)), closes [#123](https://github.com/rknightion/meraki-dashboard-ha/issues/123)
* enhance Meraki dashboard sensor logic and structure ([919c3c3](https://github.com/rknightion/meraki-dashboard-ha/commit/919c3c3afd92d5fa746edb7a674d5ba7145ed874))
* enhance styles and update links ([b810d9f](https://github.com/rknightion/meraki-dashboard-ha/commit/b810d9f611e36e0700b86172d09ac90e4df3c1bf))
* migrate MT refresh service from per-device to batch API ([747f1dc](https://github.com/rknightion/meraki-dashboard-ha/commit/747f1dc4f8431f51d4fcf3239286a2ec064f61e7))
* modernize development script to use uv and improve Home Assistant setup ([e79ae2b](https://github.com/rknightion/meraki-dashboard-ha/commit/e79ae2b2340374c10c247237867a7edc8ee4902b))
* move MkDocs dependencies to dev requirements ([0167387](https://github.com/rknightion/meraki-dashboard-ha/commit/0167387a85e6326ed62fd81edc8bfc016c987e1b))
* remove obsolete PoE sensor and enhance data retrieval ([c6624a1](https://github.com/rknightion/meraki-dashboard-ha/commit/c6624a1cc31757b4b719436058d94f5f87ef92dc))
* remove problematic release-drafter in favor of generate-release-notes ([32b8d4d](https://github.com/rknightion/meraki-dashboard-ha/commit/32b8d4d09d90e45f6d07dd7c1e606ddd2f0c591e))
* remove unused port statistics collection for switch devices ([6a9976c](https://github.com/rknightion/meraki-dashboard-ha/commit/6a9976c0fda438fd26c718608720fa2a0391a696))
* remove unused translation strings ([ccd5ce9](https://github.com/rknightion/meraki-dashboard-ha/commit/ccd5ce9b200baf36eb16d98e20282861e3c901c4))
* replace direct API calls with organization hub cache for ethernet status ([c6e63c6](https://github.com/rknightion/meraki-dashboard-ha/commit/c6e63c6a12e3a5ec2a35170d6a640f9f650bd11a))
* **sensors:** change MT energy sensor from TOTAL to TOTAL_INCREASING ([27513de](https://github.com/rknightion/meraki-dashboard-ha/commit/27513de24263b474cb076349c9a58821dfbdb833))
* **sensor:** update MT refresh service to use official SDK method ([2564a0e](https://github.com/rknightion/meraki-dashboard-ha/commit/2564a0e4328caabd829fad1cb1f5fc4ac131f032))
* simplify statistics metadata handling ([e764f0c](https://github.com/rknightion/meraki-dashboard-ha/commit/e764f0cfa388c335755a578c2d661e9e99723c4b))
* split release workflows for asset management ([318a729](https://github.com/rknightion/meraki-dashboard-ha/commit/318a729db1908852b872b33c43ee4ac47c938f53))
* streamline changelog update script ([9274fad](https://github.com/rknightion/meraki-dashboard-ha/commit/9274fada1a09b206f76addb560f4bdc0e9ad4a43))
* streamline VS Code extensions and tasks configuration ([d5a89cd](https://github.com/rknightion/meraki-dashboard-ha/commit/d5a89cd0ebb0a90449998ae9004c4949988b494f))
* switch energy sensor to Wh measurement ([22a64f3](https://github.com/rknightion/meraki-dashboard-ha/commit/22a64f3ad6864672269dde38e685bc45e9fbc1a9))
* update bandit workflow and simplify MS/MR device implementations ([92403ab](https://github.com/rknightion/meraki-dashboard-ha/commit/92403ab8e6bfc66f4092b4038e592e0ffb213ade))
* update device identifier logic ([41742dd](https://github.com/rknightion/meraki-dashboard-ha/commit/41742dd276ed6af8f1c516f22dcf8a9d90230050))


### Build System

* add Home Assistant as development dependency ([4f1c016](https://github.com/rknightion/meraki-dashboard-ha/commit/4f1c016883e18b5beb93b98d324545e31d4ec1d5))

## [0.31.0](https://github.com/rknightion/meraki-dashboard-ha/compare/v0.30.0...v0.31.0) (2025-11-07)


### Features

* expand device type support in device selection flow ([231b5f6](https://github.com/rknightion/meraki-dashboard-ha/commit/231b5f685923d5b03dbe4cc0a790a618049ba8e7))


### Bug Fixes

* adjust minimum scan interval to 30 seconds for better responsiveness ([6ff4d0c](https://github.com/rknightion/meraki-dashboard-ha/commit/6ff4d0c41fbe8df0754efd1c332928f69a6bb032))
* correct water sensor data extraction and add memory usage metrics ([b5f90f8](https://github.com/rknightion/meraki-dashboard-ha/commit/b5f90f83cdbfce7ebb1b6ffcb98d52511622bc6a))
* improve reauth flow entry lookup mechanism ([f5a2353](https://github.com/rknightion/meraki-dashboard-ha/commit/f5a235349c3bb8c10b9ca9b008df2051ba4db3a9))


### Performance Improvements

* optimize caching strategy in network hub data retrieval ([2dbc5e4](https://github.com/rknightion/meraki-dashboard-ha/commit/2dbc5e46114013aca6cd227bd0be2d0311493f9c))


### Miscellaneous Chores

* add secrets baseline configuration for security scanning ([a1936f4](https://github.com/rknightion/meraki-dashboard-ha/commit/a1936f4d10a63b320eda3dd0619e1bd4b55e4ecc))
* **deps:** lock file maintenance ([9645394](https://github.com/rknightion/meraki-dashboard-ha/commit/9645394596fe51af2e52c60f692e7c5d4a63e44d))
* **deps:** lock file maintenance ([bde285b](https://github.com/rknightion/meraki-dashboard-ha/commit/bde285b628e0fe3b293bed45aea7542636135196))
* **deps:** update actions/upload-artifact action to v5 ([24a3fdd](https://github.com/rknightion/meraki-dashboard-ha/commit/24a3fdd7eb6b7e91e2128f1aeb65d3b323e45994))
* **deps:** update actions/upload-artifact action to v5 ([1b4c9eb](https://github.com/rknightion/meraki-dashboard-ha/commit/1b4c9eb5145c1c5eeffd22fc2a80b4efe752ec73))
* **deps:** update astral-sh/setup-uv action to v7.1.2 ([e0e79c3](https://github.com/rknightion/meraki-dashboard-ha/commit/e0e79c35632e99bb98fd7901841aa669dcb761c9))
* **deps:** update astral-sh/setup-uv action to v7.1.2 ([82a77a1](https://github.com/rknightion/meraki-dashboard-ha/commit/82a77a132619479ed8c2daffb96cb4c8decde4ee))
* **deps:** update dependency homeassistant-stubs to v2025.11.0 ([c8feb18](https://github.com/rknightion/meraki-dashboard-ha/commit/c8feb1829203312e602141a49e314ff059d0a662))
* **deps:** update dependency homeassistant-stubs to v2025.11.0 ([f4a5e03](https://github.com/rknightion/meraki-dashboard-ha/commit/f4a5e031bfd7d457c25371f5e3d054fcbbf35c65))
* **deps:** update github/codeql-action action to v4.31.2 ([#152](https://github.com/rknightion/meraki-dashboard-ha/issues/152)) ([694c7d8](https://github.com/rknightion/meraki-dashboard-ha/commit/694c7d808720df4f9f10624a2f045d510b9632ca))
* **deps:** update github/codeql-action digest to 0499de3 ([#151](https://github.com/rknightion/meraki-dashboard-ha/issues/151)) ([f93d596](https://github.com/rknightion/meraki-dashboard-ha/commit/f93d59609665fa9c8bfafc65e96dae40106a52bc))
* **deps:** update googleapis/release-please-action action to v4.4.0 ([#160](https://github.com/rknightion/meraki-dashboard-ha/issues/160)) ([d30e330](https://github.com/rknightion/meraki-dashboard-ha/commit/d30e330edad76387b41793f5f30668cf5ff503e8))
* **deps:** update home-assistant/actions digest to 8ca6e13 ([#155](https://github.com/rknightion/meraki-dashboard-ha/issues/155)) ([e263b81](https://github.com/rknightion/meraki-dashboard-ha/commit/e263b81dbce49571801a08bb8167f3056282b643))
* **deps:** update mcr.microsoft.com/devcontainers/python docker tag to v3.14 ([64be4d5](https://github.com/rknightion/meraki-dashboard-ha/commit/64be4d532f3935384cd1cd7066a340d467f01e17))
* **deps:** update mcr.microsoft.com/devcontainers/python docker tag to v3.14 ([a696e5b](https://github.com/rknightion/meraki-dashboard-ha/commit/a696e5bcfc9a2464dfa3a124d57fc9cb68fa8be1))
* **deps:** update step-security/harden-runner action to v2.13.2 ([1bf5877](https://github.com/rknightion/meraki-dashboard-ha/commit/1bf5877ec59df2c48f6f43b41a92cfb76c6f8376))
* **deps:** update step-security/harden-runner action to v2.13.2 ([f9f32aa](https://github.com/rknightion/meraki-dashboard-ha/commit/f9f32aa3044151fefd444f9cb4fda63a8c0f01f1))
* improve type safety and code quality ([fd2602e](https://github.com/rknightion/meraki-dashboard-ha/commit/fd2602ead2f3697132640ca06d530290c6bb52e4))
* **release:** remove pull request header from config ([5595d0c](https://github.com/rknightion/meraki-dashboard-ha/commit/5595d0cb3ba8252ffdba023f1c4c8262c9f6a35a))
* remove redundant pre-commit hooks ([1d92d86](https://github.com/rknightion/meraki-dashboard-ha/commit/1d92d8683f3edc4e32f70bfe356c07865b598cf3))
* replace custom release workflow with release-please ([e40a2b9](https://github.com/rknightion/meraki-dashboard-ha/commit/e40a2b94a3f5fc51639251813a22e3fa1562dbff))
* replace custom release workflow with release-please ([9c2e808](https://github.com/rknightion/meraki-dashboard-ha/commit/9c2e808be48acb24802eaeeeefacad15f8a15f3f))


### Code Refactoring

* remove unused port statistics collection for switch devices ([6a9976c](https://github.com/rknightion/meraki-dashboard-ha/commit/6a9976c0fda438fd26c718608720fa2a0391a696))

## [Unreleased]


## [0.30.0] - 2025-11-07


### 🚀 Features
- add organization-level ethernet status caching for wireless devices
- enhance user interface strings with detailed descriptions and MT sensor support
- implement configurable MT refresh service with interval support
- enhance config flow with MT refresh settings and improved UX
- add MT refresh service configuration and interval validation

### 🧰 Maintenance
747f1dc refactor: migrate MT refresh service from per-device to batch API
ac98af7 chore: update ruff pre-commit hook to v0.14.4
c6e63c6 refactor: replace direct API calls with organization hub cache for ethernet status

### 📚 Documentation
- restructure documentation with focused CLAUDE.md guidance

### ✅ Tests
- update transformer tests to reflect actual behavior
- fix wireless data transformer client count assertion
- add test fixtures and unit tests for wireless ethernet status functionality
- replace mock fixtures with real API response data
- add comprehensive test suite with fixtures and coverage improvements
- expand configuration schema tests with MT refresh validation
- add comprehensive MT refresh service test coverage

### 📋 Other Changes
- (i18n): add German, Spanish, and French translations


## [0.28.2] - 2025-10-18



### 🐛 Bug Fixes
- fox indoor air quality support and expand fallback capabilities

### 🧰 Maintenance
e19a9e1 chore: update project dependencies to latest versions
e79ae2b refactor: modernize development script to use uv and improve Home Assistant setup
4f1c016 build: add Home Assistant as development dependency
d5a89cd refactor: streamline VS Code extensions and tasks configuration
4b02b62 chore: update gitignore to track VS Code defaults while ignoring user settings

### 🚀 Dev Features
- enhance Home Assistant development configuration
- add VS Code workspace settings template for Home Assistant development
- add comprehensive VS Code debug configurations for Home Assistant development

### 📋 Other Changes
- Merge remote-tracking branch 'origin/main'


## [0.28.1] - 2025-10-18


### 🐛 Bug Fixes
- correct MT device model capabilities mapping

### 🧰 Maintenance
70293a4 chore(deps): update dependency homeassistant-stubs to v2025.10.3
121f936 chore(deps): update github/codeql-action digest to 16140ae (#145)
3860490 chore(deps): update github/codeql-action action to v4.30.9
c059a47 chore(deps): lock file maintenance (#142)
05914bc chore(deps): update astral-sh/setup-uv action to v7.1.0 (#141)
b9513cd chore(deps): update dependency homeassistant-stubs to v2025.10.2 (#140)
faa74cb chore(deps): update actions/dependency-review-action action to v4.8.1 (#139)
3bbd594 chore(deps): update github/codeql-action action to v4.30.8 (#138)
61ad7ac chore(deps): update github/codeql-action digest to f443b60 (#137)
3b0209d chore(deps): update github/codeql-action action to v4 (#136)
d538ae6 chore(deps): update astral-sh/setup-uv action to v7 (#135)
e9e1be4 chore(deps): update github/codeql-action action to v3.30.7 (#134)
7026902 chore(deps): update github/codeql-action digest to a8d1ac4 (#133)
c438dc3 chore(deps): update home-assistant/actions digest to e5c9826 (#131)
030331e chore(deps): lock file maintenance (#130)
e1b8b89 chore(deps): update dependency homeassistant-stubs to v2025.10.1 (#126)
04cc8b8 chore(deps): update actions/stale action to v10.1.0 (#129)
fdb636d chore(deps): update github/codeql-action action to v3.30.6 (#128)
22aa593 chore(deps): update github/codeql-action digest to 64d10c1 (#127)
09f3d01 chore(deps): update peter-evans/repository-dispatch action to v4 (#125)
4d52988 chore(deps): update ossf/scorecard-action action to v2.4.3 (#124)
35f2ca0 chore(deps): update astral-sh/setup-uv action to v6.8.0 (#123)
a1e82cb chore(deps): lock file maintenance (#122)
53816de chore(deps): update actions/dependency-review-action action to v4.8.0 (#121)
d902fc0 chore(deps): update github/codeql-action action to v3.30.5 (#120)
abd45c0 chore(deps): update github/codeql-action digest to 3599b3b (#119)
07ed54c chore(deps): update github/codeql-action action to v3.30.4 (#118)
7a64d5b chore(deps): update github/codeql-action digest to 303c0ae (#117)
476a173 chore(deps): lock file maintenance (#116)
ed6db0d chore(deps): update dependency homeassistant-stubs to v2025.9.4 (#115)
a6b5e06 chore(deps): update zizmorcore/zizmor-action action to v0.2.0 (#114)
ed52957 chore(deps): lock file maintenance (#113)
2a310b3 chore(deps): update dependency homeassistant-stubs to v2025.9.3 (#111)
95e3f17 chore(deps): update astral-sh/setup-uv action to v6.7.0 (#112)
9ac1dae chore(deps): update home-assistant/actions digest to 342664e (#110)
3dc4602 chore(deps): update github/codeql-action action to v3.30.3 (#109)
151b383 chore(deps): update github/codeql-action digest to 192325c (#108)
296e4e0 chore(deps): update step-security/harden-runner action to v2.13.1 (#107)
ca9576b chore(deps): update github/codeql-action action to v3.30.2 (#106)
89eabd3 chore(deps): update github/codeql-action digest to d3678e2 (#105)
cfc04a5 chore(deps): lock file maintenance (#104)
97e549a chore(deps): update actions/stale action to v10 (#103)
cb8422c chore(deps): update actions/setup-python action to v6 (#102)
2353fd6 chore(deps): update github/codeql-action action to v3.30.1 (#101)
cf3fe02 chore(deps): update dependency homeassistant-stubs to v2025.9.1 (#100)
3e7ec1a chore(deps): update codecov/codecov-action action to v5.5.1 (#99)
ea8cf9d chore(deps): update astral-sh/setup-uv action to v6.6.1 (#98)
217b5ad chore(deps): update github/codeql-action digest to f1f6e5f (#97)

### 📋 Other Changes
- Merge remote-tracking branch 'origin/renovate/homeassistant-stubs-2025.x'
- Merge pull request #146 from rknightion/renovate/github-codeql-action-4.x


## [0.28.0] - 2025-08-29


### 🚀 Features
- increase MR and MS device refresh intervals to 10 minutes (it's what they were previously and it reduces the chance of getting rate limited with the increased MT polling frequency)


## [0.27.2] - 2025-08-29


### 🐛 Bug Fixes
- increase minimum update interval from 7.5s to 30s


## [0.27.1] - 2025-08-29


### 🧰 Maintenance
2564a0e refactor(sensor): update MT refresh service to use official SDK method


## [0.27.0] - 2025-08-29


### 🚀 Features
- improve device-specific configuration UI
- implement fast refresh mode for MT15/MT40 devices which will force them to get much more realtime data (~15 second polling)

### 🧰 Maintenance
351a508 chore(deps): update actions/dependency-review-action action to v4.7.3 (#96)
87eb4d5 chore(deps): update actions/ai-inference action to v2.0.1 (#95)
e5d3f12 chore(deps): lock file maintenance (#94)
a920082 chore(deps): update github/codeql-action action to v3.29.11 (#81)
74f882e chore(deps): pin dependencies (#93)
4300718 chore(deps): update home-assistant/actions digest to 72e1db9 (#80)
2c39a24 chore(deps): bump astral-sh/setup-uv from 6.5.0 to 6.6.0
3e95716 chore(deps): bump mkdocs-material from 9.6.17 to 9.6.18
d35def3 chore(deps): bump homeassistant-stubs from 2025.8.2 to 2025.8.3
372d112 chore(deps): bump ruff from 0.12.9 to 0.12.10
7fcb027 chore(deps): bump codecov/codecov-action from 5.4.3 to 5.5.0
c0665b0 chore(deps): bump homeassistant-stubs from 2025.8.1 to 2025.8.2
ade020f chore(deps): bump actions/dependency-review-action from 4.7.1 to 4.7.2
26fb0e8 chore(deps): bump mkdocs-material from 9.6.16 to 9.6.17
57b1564 chore(deps): bump actions/ai-inference from 1.2.8 to 2.0.0
fc22186 chore(deps): bump zizmorcore/zizmor-action from 0.1.1 to 0.1.2
26072b6 chore(deps): update zizmorcore/zizmor-action action to v0.1.2
2b37db0 chore(deps): update github/codeql-action action to v3.29.9
3016abf chore(deps): bump actions/checkout from 4 to 5

### 📋 Other Changes
- set all-checks job
- disable dependabot
- update renovate config
- Merge pull request #92 from rknightion/dependabot/github_actions/astral-sh/setup-uv-6.6.0
- Merge pull request #91 from rknightion/dependabot/uv/mkdocs-material-9.6.18
- Merge pull request #90 from rknightion/dependabot/uv/homeassistant-stubs-2025.8.3
- Merge pull request #89 from rknightion/dependabot/uv/ruff-0.12.10
- Merge pull request #87 from rknightion/dependabot/github_actions/codecov/codecov-action-5.5.0
- Merge pull request #85 from rknightion/dependabot/uv/homeassistant-stubs-2025.8.2
- Merge pull request #83 from rknightion/dependabot/github_actions/actions/dependency-review-action-4.7.2
- Merge pull request #79 from rknightion/dependabot/uv/mkdocs-material-9.6.17
- Merge remote-tracking branch 'origin/dependabot/github_actions/actions/ai-inference-2.0.0'
- Merge remote-tracking branch 'origin/main'
- Merge remote-tracking branch 'origin/dependabot/github_actions/zizmorcore/zizmor-action-0.1.2'
- Merge remote-tracking branch 'origin/dependabot/github_actions/actions/checkout-5'
- Merge remote-tracking branch 'origin/renovate/github-codeql-action-3.x'
- Merge remote-tracking branch 'origin/renovate/zizmorcore-zizmor-action-0.x'


## [0.26.0] - 2025-08-14


### 🚀 Fixes
- FIx energy total sensors to avoid energy dashboard negative usage
- remove all-checks-pass job and update dependencies

### 🧰 Maintenance
87f66fb chore(deps): update development dependencies and format code
27513de refactor(sensors): change MT energy sensor from TOTAL to TOTAL_INCREASING
c9cb0ef chore(deps): bump astral-sh/setup-uv from 6.4.3 to 6.5.0
a46b9bc chore(deps): bump homeassistant-stubs from 2025.8.0 to 2025.8.1
df05769 chore(deps): update github/codeql-action action to v3.29.8
b604f13 chore(deps): bump actions/ai-inference from 1.2.7 to 1.2.8
60796d0 chore(deps): bump ruff from 0.12.7 to 0.12.8
2379bc2 chore(deps): bump homeassistant-stubs from 2025.7.3 to 2025.8.0
b8fcb12 chore(deps): bump actions/ai-inference from 1.2.4 to 1.2.7
d1e1791 chore(deps): bump pytest-homeassistant-custom-component
ee1930b chore(deps): bump actions/ai-inference from 1.2.3 to 1.2.4
55db31b chore: remove deprecated guidelines and rules files
ee22490 chore(deps): bump ruff from 0.12.5 to 0.12.7

### 📋 Other Changes
- Merge pull request #75 from rknightion/dependabot/github_actions/astral-sh/setup-uv-6.5.0
- Merge pull request #72 from rknightion/dependabot/uv/homeassistant-stubs-2025.8.1
- Merge pull request #58 from rknightion/renovate/github-codeql-action-3.x
- Merge pull request #67 from rknightion/dependabot/github_actions/actions/ai-inference-1.2.8
- Merge pull request #66 from rknightion/dependabot/uv/ruff-0.12.8
- Merge pull request #65 from rknightion/dependabot/uv/homeassistant-stubs-2025.8.0
- Merge pull request #64 from rknightion/dependabot/github_actions/actions/ai-inference-1.2.7
- Merge pull request #63 from rknightion/dependabot/uv/pytest-homeassistant-custom-component-0.13.266
- Merge pull request #62 from rknightion/dependabot/github_actions/actions/ai-inference-1.2.4
- fix robot
- add robots.txt
- Merge pull request #59 from rknightion/dependabot/uv/ruff-0.12.7


## [0.25.6] - 2025-07-30


### 🐛 Bug Fixes
- optimize energy calculation with data change detection


## [0.25.5] - 2025-07-30


### 🧰 Maintenance
ccd5ce9 refactor: remove unused translation strings
61d8650 refactor(config): improve options flow UI and add API key update capability
62191ac ci: add documentation sync workflow
5a69c0a chore: update project name and domain pattern
0167387 refactor: move MkDocs dependencies to dev requirements
90f7bdb chore: change license from MIT to Apache 2.0

### 📚 Documentation
- update mermaid diagram syntax in documentation
- fix documentation links and update Cloudflare domain

### ✅ Tests
- extend coverage for config migration

### 📋 Other Changes
- Merge remote-tracking branch 'origin/main'
- Update README.md
- docs updates
- remove 404
- build
- fix
- fix
- fix missing /
- fix site routing
- fix route
- fix wrangler proj name
- remove polyfill
- Merge pull request #57 from rknightion/codex/increase-test-coverage-for-custom-component
- Merge branch 'main' into codex/increase-test-coverage-for-custom-component
- Merge remote-tracking branch 'origin/main'


## [0.25.4] - 2025-07-27


### 🐛 Bug Fixes
- improve GitHub Actions authentication for workflows


## [0.25.1] - 2025-07-27


### 🧰 Maintenance
92403ab refactor: update bandit workflow and simplify MS/MR device implementations


## [0.25.0] - 2025-07-27


### 🚀 Features
- add device type filtering options

### 🧰 Maintenance
65696c8 ci: improve draft release cleanup in GitHub workflow
8c7051c ci: enhance GitHub workflows for release management
700d44d ci: remove redundant build job from update-version workflow


## [0.24.30] - 2025-07-27


### 🧰 Maintenance
fb1feff ci: remove GitHub Pages deployment from version update workflow

### 📋 Other Changes
- Merge remote-tracking branch 'origin/main'


## [0.24.29] - 2025-07-27


### 🚀 Features
- add new sensors for Meraki MR and MS devices


## [0.24.28] - 2025-07-27


### 🧰 Maintenance
334c7cc chore(deps): update dependency wrangler to v4

### 📚 Documentation
- add AGENTS.md with project guidelines and architecture

### 📋 Other Changes
- Merge remote-tracking branch 'origin/renovate/wrangler-4.x'
- Remove markdownlint and fix Lambda functions
- Auto stash before merge of "main" and "origin/main"
- Auto stash before merge of "main" and "origin/main"
- Merge remote-tracking branch 'origin/main'
- enhance: expand integration with comprehensive documentation and new device metrics


## [0.24.24] - 2025-07-27


### 🐛 Bug Fixes
- improve configuration migration process

### 📋 Other Changes
- Merge remote-tracking branch 'origin/main'


## [0.24.23] - 2025-07-27


### 🚀 Features
- add memory usage metrics for MR and MS devices
- Enhance device status information retrieval
- Adds Bluetooth clients sensor and related data handling
- enhance device monitoring and traffic handling
- improve graceful handling of missing sensor readings
- implement dynamic MT device capability discovery
- Add configurable tiered refresh intervals for data
- Introduces Meraki Dashboard integration with multi-device support
- Enable automatic application of API guidelines and code style rules

### 🐛 Bug Fixes
- release notes generation with reliable versioning
- Pin pytest-asyncio version
- Refactor and improve project structure and documentation
- update measurement units and improve event logging
- reduce scan and refresh intervals to 1 minute
- refactor sensor via_device identification
- update tests to match corrected MT device capabilities
- Enhance performance and consistency in Meraki integration

### 🧰 Maintenance
6cc5804 chore: fix
c6435a5 chore(deps): update dependency wdm to "~> 0.2.0"
1a07dfd chore(deps): update dependency http_parser.rb to "~> 0.8.0"
5866bd6 ci: Configures CodeQL advanced code scanning
c880baa chore: Updates pre-commit hooks
395d056 chore(deps): bump ossf/scorecard-action from 2.4.0 to 2.4.2
f12125c ci(deps): bump actions/first-interaction from 1 to 2
919c3c3 refactor: enhance Meraki dashboard sensor logic and structure
56c146f chore: fix ci
adff896 chore: enhance configuration migration and validation
2a63ce0 chore: Refactors Meraki integration for improved type safety
c6624a1 refactor: remove obsolete PoE sensor and enhance data retrieval
41742dd refactor: update device identifier logic

### 📋 Other Changes
- Merge pull request #52 from rknightion/renovate/wdm-0.x
- Merge pull request #51 from rknightion/renovate/http_parser.rb-0.x
- Create codeql.yml
- no codeql
- Merge pull request #55 from rknightion/dependabot/github_actions/ossf/scorecard-action-2.4.2
- Merge pull request #54 from step-security-bot/chore/GHA-270956-stepsecurity-remediation
- [StepSecurity] Apply security best practices
- Migrates from Poetry to uv for dependency management, resulting in faster and more efficient dependency resolution.
- Merge pull request #47 from rknightion/dependabot/pip/ruff-0.12.5
- Merge pull request #45 from rknightion/dependabot/github_actions/actions/first-interaction-2
- Merge pull request #44 from rknightion/dependabot/pip/mypy-1.17.0
- Merge pull request #42 from rknightion/dependabot/pip/bandit-1.8.6
- Create renovate.json
- Merge pull request #39 from rknightion/dependabot/pip/pip-2c7469b053
- Merge pull request #41 from fossabot/add-license-scan-badge
- deps(deps-dev): bump ruff from 0.12.1 to 0.12.5
- deps(deps-dev): bump mypy from 1.16.1 to 1.17.0
- deps(deps-dev): bump bandit from 1.8.5 to 1.8.6
- Add license scan report and status
- Refactors constants handling for Meraki integration
- Add advanced channel utilization metrics for MR devices
- Refactors sensor data handling and improves configuration intervals
- backup
- Enhances logging and coordination handling
- Refactors Meraki Dashboard integration with base classes and factories
- update refactor
- Adds new sensors for client data usage in organization hubs
- deps(deps): bump urllib3 from 1.26.20 to 2.5.0 in the pip group
- Refactors alert handling to use network-level summaries
- Enhance test workflow and improve device data handling
- Add enhanced error handling and testing improvements
- Improve device matching and event processing
- Add and update documentation for API optimization strategies
- update lockfile
- Refactors configuration handling and updates licensing model logic


## [0.24.22] - 2025-06-28

### 🧰 Maintenance
- update ruff version and enhance config flow options


## [0.24.21] - 2025-06-27

### 🐛 Bug Fixes
- pr labeller


## [0.24.20] - 2025-06-26

### 🧰 Maintenance
- switch energy sensor to Wh measurement


## [0.24.19] - 2025-06-26

### 🐛 Bug Fixes
- adjust version update and energy sensor logic


## [0.24.18] - 2025-06-26

### 🐛 Bug Fixes
- codecov


## [0.24.17] - 2025-06-26

### 🚀 Features
- enhance energy sensor precision and add reset logic
### 🐛 Bug Fixes
- convert energy state from kWh to Wh during restoration
### 🧰 Maintenance
- update zizmor hook to v1.10.0


## [0.24.16] - 2025-06-25

proper hacky


## [0.24.15] - 2025-06-25

### 🐛 Bug Fixes
- manual sleepz


## [0.24.14] - 2025-06-25

### 🐛 Bug Fixes
- ordering


## [0.24.13] - 2025-06-25

### 🐛 Bug Fixes
- gh pages maybe
- add some sleeps


## [0.24.12] - 2025-06-25

### 🚀 Features
- add daily Jekyll deployment schedule


## [0.24.11] - 2025-06-25

### 🚀 Features
- auto-run release notes generation on pushes to main
- enhance release note generation for direct commits
### 🐛 Bug Fixes
- handle existing tags in release note generation
### 🧰 Maintenance
- remove node_modules from search exclusion
- remove problematic release-drafter in favor of generate-release-notes


## [0.24.10] - 2025-06-25

* No changes


## [0.24.9] - 2025-06-25

* No changes


## [0.24.8] - 2025-06-25

* No changes


## [0.24.7] - 2025-06-25

**Full Changelog**: https://github.com/rknightion/meraki-dashboard-ha/compare/v0.24.6...v0.24.7


## [0.24.6] - 2025-06-25

* No changes


## [0.23.0] - 2025-06-22

### Fixed
- Enhanced release workflow and removed obsolete sensor


## [0.22.0] - 2025-06-22

### Fixed
- Enhanced release workflow and removed obsolete sensor

---

For releases prior to v0.22.0, see the [GitHub Releases page](https://github.com/rknightion/meraki-dashboard-ha/releases).

---

## Support

- **Questions**: Check our [FAQ](faq) or see the troubleshooting section on the [main page](/)
- **Issues**: Report bugs on [GitHub Issues]({{ site.repository }}/issues)
- **Discussions**: Join the conversation on [GitHub Discussions]({{ site.repository }}/discussions)

## Links

- **[Releases]({{ site.repository }}/releases)** - Download specific versions
- **[Release Notes]({{ site.repository }}/releases)** - Detailed release information
