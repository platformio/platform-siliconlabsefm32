# Silicon Labs EFM32: development platform for [PlatformIO](http://platformio.org)
[![Build Status](https://travis-ci.org/platformio/platform-siliconlabsefm32.svg?branch=develop)](https://travis-ci.org/platformio/platform-siliconlabsefm32)
[![Build status](https://ci.appveyor.com/api/projects/status/26esqje4bp0m2614/branch/develop?svg=true)](https://ci.appveyor.com/project/ivankravets/platform-siliconlabsefm32/branch/develop)

Silicon Labs EFM32 Gecko 32-bit microcontroller (MCU) family includes devices that offer flash memory configurations up to 256 kB, 32 kB of RAM and CPU speeds up to 48 MHz. Based on the powerful ARM Cortex-M core, the Gecko family features innovative low energy techniques, short wake-up time from energy saving modes and a wide selection of peripherals, making it ideal for battery operated applications and other systems requiring high performance and low-energy consumption.

* [Home](http://platformio.org/platforms/siliconlabsefm32) (home page in PlatformIO Platform Registry)
* [Documentation](http://docs.platformio.org/page/platforms/siliconlabsefm32.html) (advanced usage, packages, boards, frameworks, etc.)

# Usage

1. [Install PlatformIO](http://platformio.org)
2. Create PlatformIO project and configure a platform option in [platformio.ini](http://docs.platformio.org/page/projectconf.html) file:

## Stable version

```ini
[env:stable]
platform = siliconlabsefm32
board = ...
...
```

## Development version

```ini
[env:development]
platform = https://github.com/platformio/platform-siliconlabsefm32.git
board = ...
...
```

# Configuration

Please navigate to [documentation](http://docs.platformio.org/page/platforms/siliconlabsefm32.html).
