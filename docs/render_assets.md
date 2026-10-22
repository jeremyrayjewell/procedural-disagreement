# Render assets

Every data and media file the final render, its encode and its checks read (code is in Git).
Made by `tools/assets_manifest.py`; check a copy with `python tools/assets_manifest.py --verify`.

| Path | Group | Size | SHA-256 | Purpose |
| --- | --- | --- | --- | --- |
| `audio/mix4_master_24bit.wav` | source media | 74.1 MB | `2eccd7ec2d01a77164cf396b0fcf2653a3a484850af0d0195b1b8f67425ec46d` | The definitive audio master (280.000 s, 44.1 kHz, 24-bit PCM stereo): the film's soundtrack, muxed by tools/render.py when encoding, and the source analysis/audio_features.json was measured from |
| `assets/video/crt/01.mp4` | source media | 8.4 MB | `cf6292c17daee838c410977764c25d94a43ce6126f549f6ac7e13e33e866c5ce` | The director's CRT footage, clips 01-08: the source of the CRT stream (tools/make_crt_video.py) |
| `assets/video/crt/02.mp4` | source media | 10.3 MB | `9a29c24a77e0e6c6da4ead172dcf47bd670a42730c5c9f5051898756a38c7cd8` | The director's CRT footage, clips 01-08: the source of the CRT stream (tools/make_crt_video.py) |
| `assets/video/crt/03.mp4` | source media | 10.3 MB | `6c7b99e01076273df6134282b3b6d82862bb8f5c1c3e40cc87f677fcbb7a6597` | The director's CRT footage, clips 01-08: the source of the CRT stream (tools/make_crt_video.py) |
| `assets/video/crt/04.mp4` | source media | 10.9 MB | `687aae6e0d7fd992d6e1d82e5746bf0a06d275257ea9ab0571e23dce7612a594` | The director's CRT footage, clips 01-08: the source of the CRT stream (tools/make_crt_video.py) |
| `assets/video/crt/05.mp4` | source media | 7.9 MB | `44efe485674010ddfe55934bd791f2a309ba66dcd202f2d01d19901e43680908` | The director's CRT footage, clips 01-08: the source of the CRT stream (tools/make_crt_video.py) |
| `assets/video/crt/06.mp4` | source media | 12.7 MB | `fb948f0ef30e3994c9a8316026600f40954d47731e3402c0fa047c6ccb5320a2` | The director's CRT footage, clips 01-08: the source of the CRT stream (tools/make_crt_video.py) |
| `assets/video/crt/07.mp4` | source media | 17.4 MB | `0b312b0cdeff4fb85e9dbea3a8d0bd637d7420e5833d79ace8d59ade2effd726` | The director's CRT footage, clips 01-08: the source of the CRT stream (tools/make_crt_video.py) |
| `assets/video/crt/08.mp4` | source media | 15.9 MB | `ed8973b06567f50c3e6a5b6259cdf83b03ab9f161e0f6a2fafbc25059f9f3cde` | The director's CRT footage, clips 01-08: the source of the CRT stream (tools/make_crt_video.py) |
| `cues/poc_0035_0105.json` | render | 21.9 kB | `46bf795262a0305db141e47a752d64644e648b707c22379c3c42fc644a94e0b0` | The directorial cue file: every authored event time |
| `analysis/audio_features.json` | render | 1.2 MB | `499d0a3710c4fd0cd6126f43394e587e666e247c5b9e98d3247edd375339b1ab` | The soundtrack measured (tools/analyze_audio.py, from the audio master: its SHA-1 is recorded inside): the envelopes the light leans with |
| `assets/lyrics/layout.json` | render | 0.1 MB | `33085eb389b2ef8ebc4ba568a491572e6f4b42cf40429b3064de72a548621dd4` | Where every sung line is shown (tools/lyric_layout.py) |
| `assets/fonts/unifont/unifont_all-17.0.05.hex.gz` | render | 1.8 MB | `7b182454966046d35482469b979edce7d262fab5c53c2180e9b1fbb5d0b5e574` | GNU Unifont 17.0.05, the lyric's only glyph source (no fallback) |
| `assets/fonts/unifont/unifont_all-17.0.05.hex.gz.sig` | licence and provenance | 0.6 kB | `7acec1426bd7f5f8b1abea20c0fe0b182a3ddfa0af3cba87dffd5f967650733a` | GNU's signature for the font file |
| `assets/fonts/unifont/COPYING` | licence and provenance | 48.4 kB | `cd2785c2b8e0a01d203560265b2d2d47cdb1401d2707d25918ac5531bcdba947` | Unifont licence (GPL v2+ with the font embedding exception) |
| `assets/fonts/unifont/OFL-1.1.txt` | licence and provenance | 4.3 kB | `869692af094c57fb7258c57fe26820c759319603321d0ffeb278de3651763ded` | Unifont licence (SIL Open Font License 1.1) |
| `assets/fonts/unifont/SOURCE.txt` | licence and provenance | 0.6 kB | `3a8d333070af3720cf335e88cc59b19644c8c28f502e4bc005752ced9a2236d2` | Where the font came from |
| `assets/video/crt/canvas/stream.mp4` | render | 58.3 MB | `463993dd0723f01b962d03e202dead30ffbc5b302a18cff794427a5570085c2b` | The CRT stream every screen plays (made from clips 01-08 by tools/make_crt_video.py; approved 2026-10-22) |
| `assets/video/crt/canvas/manifest.json` | render | 1.5 kB | `eee8086827ad12f8a470ecf4e280ab327ca89e37d8cfef02ee3b01217caf496e` | Which screen starts on which clip of the stream |
| `assets/textures/room_shell/retro_floor_01/modulation.png` | render | 1.8 kB | `ba935552d4d836bffa70a31ffaa6296688d174d2615f1789bced2a5fc08c6b87` | The look's low-resolution grey maps (tools/make_retro_maps.py) |
| `assets/textures/room_shell/retro_level_01/modulation.png` | render | 1.9 kB | `c5d787fd91eb780871a132cc3d065e3a56940dec84ac3c09865a5b4786eb51ac` | The look's low-resolution grey maps (tools/make_retro_maps.py) |
| `assets/textures/room_shell/retro_prop_01/modulation.png` | render | 0.2 kB | `e261e5ecda761a3b02bdf5d79db536423f3929ecaa39c1e0217524b18f28e0bb` | The look's low-resolution grey maps (tools/make_retro_maps.py) |
| `assets/textures/room_shell/retro_ps1_01/modulation.png` | render | 1.8 kB | `0bcb2e2dc0772456395ab67de43465e13e5ee83b919b610d2b27c1b058d6bbdf` | The look's low-resolution grey maps (tools/make_retro_maps.py) |
| `assets/textures/room_shell/retro_waste_01/modulation.png` | render | 1.9 kB | `3931346500afbcb51742f6b4a72e3839101580f2f1b34bea4b451c30e82bfe9e` | The look's low-resolution grey maps (tools/make_retro_maps.py) |
| `tests/reference/locked_0000_0035.json` | checks | 26.6 MB | `b01ff6b7efa8d188dc341f534a4635819be08b746669a576efe4bb38ad5283fc` | The recorded locked sequences tools/check.py compares against |
| `tests/reference/locked_0035_0105.json` | checks | 1.0 MB | `f1a2d7aec0f6147d1a2c67b55af02d1b3ea46917f5718ad286e9e5aa3010a498` | The recorded locked sequences tools/check.py compares against |
| `tests/reference/locked_0105_0120.json` | checks | 25.2 MB | `4e2c2e294560205a25f636566f928f13539ac9d8053381067beb414c268855d7` | The recorded locked sequences tools/check.py compares against |
| `tests/reference/locked_0120_0130.json` | checks | 18.9 MB | `81b90349cce3b3a08a4a3a249fca17fb11e02245c05a7701e28e4612aadd8b39` | The recorded locked sequences tools/check.py compares against |
| `tests/reference/locked_0130_0152.json` | checks | 36.2 MB | `0cc32f023a6be8dcfd45777eb7131d47571fe6d1bf61974dfc70ac7029953fc1` | The recorded locked sequences tools/check.py compares against |
| `tests/reference/locked_0152_0220.json` | checks | 24.3 MB | `63430baa269a1e1c3d97bd29d0dbc70716228ac9018a4b8592d34e78d15c9dab` | The recorded locked sequences tools/check.py compares against |
| `tests/reference/locked_0220_0300.json` | checks | 30.2 MB | `bee5ea9e8a3ac7185266f7034a682903473fc271770e84045d1f273d78d4120f` | The recorded locked sequences tools/check.py compares against |
| `tests/reference/locked_0300_0330.json` | checks | 34.9 MB | `5eb6889a3384400f205c5babbfca1e74ee73c91aedc0df550947c9df678364d3` | The recorded locked sequences tools/check.py compares against |
| `tests/reference/locked_0330_0400.json` | checks | 52.3 MB | `c14972efe0109a5c974129e3df452a4adbf7b874e69ff99a1cefd5f2c70194c0` | The recorded locked sequences tools/check.py compares against |
| `tests/reference/locked_0400_0415.json` | checks | 46.5 MB | `2f3644b34445609e5d9da14b8a2a0963e858b404a9bd7be8ec127b5e7147f4ff` | The recorded locked sequences tools/check.py compares against |
| `tests/reference/locked_0415_0425.json` | checks | 50.6 MB | `070cf0fca1846afd7d8ff121b6add4ee5865101be869798fcf28ba76802caf68` | The recorded locked sequences tools/check.py compares against |
| `tests/reference/locked_0425_0440.json` | checks | 14.1 MB | `77fdddafe457666e142efbf68a5adefaee756c4aa48916900b640d3bac0e7745` | The recorded locked sequences tools/check.py compares against |

36 files, 590.1 MB.
