![Dream Forge](docs/assets/dream-forge_banner.gif)

[![Latest Release](https://flat.badgen.net/github/release/CyWP/dream-forge)](https://github.com/carson-katri/dream-textures/releases/latest)
[![Total Downloads](https://img.shields.io/github/downloads/CyWP/dream-forge/total?style=flat-square)](https://github.com/carson-katri/dream-textures/releases/latest)

Extension of [Dream Textures](https://github.com/carson-katri/dream-textures) focusing on displacement generation for 3d modeling.
* Incorporate geometry-aware generative displacement in your 3d modeling pipeline.
* Easily create displacement designs that respond to a mesh's from.
* Edit and guide generation using UV mapping and texture painting.
* Combine with shaders for full displacement control.

*This project would have never been possible without the work done by [Carson Katri](https://github.com/carson-katri) and the [Dream Textures](https://github.com/carson-katri/dream-textures) contributors.*

# Getting Started

## Installation
Installation is the same as for Dream Textures. Download the [latest release](https://github.com/CyWP/dream-forge/releases/latest) and follow the instructions there to get up and running.

> On macOS, it is possible you will run into a quarantine issue with the dependencies. To work around this, run the following command in the app `Terminal`: `xattr -r -d com.apple.quarantine ~/Library/Application\ Support/Blender/X.X/scripts/addons/dream_textures/.python_dependencies`. This will allow the PyTorch `.dylib`s and `.so`s to load without having to manually allow each one in System Preferences.

If you want a visual guide to installation, see this video tutorial from Ashlee Martino-Tarr: https://youtu.be/kEcr8cNmqZk
> Ensure you always install the [latest version](https://github.com/CyWP/dream-forge/releases/latest) of the add-on if any guides become out of date.

## Setting Up
[Setup instructions](https://github.com/carson-katri/dream-textures/wiki/Setup) for various platforms and configurations. For Dream Forge, we recommend using the **stabilityai/stable-diffusion-2-depth** model.

## Wiki

### [Dream Forge](https://github.com/CyWP/dream-forge/wiki)
Functionalities specific to Dream Forge.
[Interface](https://github.com/CyWP/dream-forge/wiki/Interface) | [Generating Displacement](https://github.com/CyWP/dream-forge/wiki/Displacement) | [Guiding Generation](https://github.com/CyWP/dream-forge/wiki/Generation_Control) | [Compositor](https://github.com/CyWP/dream-forge/wiki/Compositor) | [Material Baking](https://github.com/CyWP/dream-forge/wiki/Baking)

### [Dream Textures](https://github.com/carson-katri/dream-textures/wiki)
Functionalities that have to do with Dream Textures.
[Image Generation](https://github.com/carson-katri/dream-textures/wiki/Image-Generation) | [Texture Projection](https://github.com/carson-katri/dream-textures/wiki/Texture-Projection) | [Inpaint/Outpaint](https://github.com/carson-katri/dream-textures/wiki/Inpaint-and-Outpaint) | [Render Engine](https://github.com/carson-katri/dream-textures/wiki/Render-Engine) | [AI Upscaling](https://github.com/carson-katri/dream-textures/wiki/AI-Upscaling) | [History](https://github.com/carson-katri/dream-textures/wiki/History)

# Compatibility
Dream Textures has been tested with CUDA and Apple Silicon GPUs. Over 4GB of VRAM is recommended.
If you have an issue with a supported GPU, please create an issue.

### Cloud Processing
If your hardware is unsupported, you can use DreamStudio to process in the cloud. Follow the instructions in the release notes to setup with DreamStudio.

# Contributing
For detailed instructions on installing from source, see the guide on [setting up a development environment](https://github.com/carson-katri/dream-textures/wiki/Setting-Up-a-Development-Environment).

# Troubleshooting

If you are experiencing trouble getting Dream Forge running, check Blender's system console (in the top left under the "Window" dropdown next to "File" and "Edit") for any error messages. First, [search the Dream Textures issues list](https://github.com/carson-katri/dream-textures/issues?q=is%3Aissue), then the [Dream Forge issues](https://github.com/CyWP/dream-forge/issues?q=is%3Aissue) with your error message and symptoms.

> **Note** On macOS there is no option to open the system console. Instead, you can get logs by opening the app *Terminal*, entering the command `/Applications/Blender.app/Contents/MacOS/Blender` and pressing the Enter key. This will launch Blender and any error messages will show up in the Terminal app.

![A screenshot of the "Window" > "Toggle System Console" menu action in Blender](docs/assets/readme-toggle-console.png)

Features and feedback are also accepted on both issues pages. If you have any issues that aren't listed, feel free to add them there!

The [Dream Textures Discord server](https://discord.gg/EmDJ8CaWZ7) also has a common issues list and strong community of helpful people, so feel free to come by for some help there as well.