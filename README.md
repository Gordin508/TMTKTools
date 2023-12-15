# Blender Addons for TMTK Creators

These [Blender](https://www.blender.org) addons are intended for use by people who want to create custom 3D objects for the video game [Planet Coaster](https://www.planetcoaster.com). Such items must be created in a format compatible with [Thememaker's Toolkit](https://thememakers-toolkit.planetcoaster.com). The addons are intended to aid creators in achieving this compatibility by automating some preparatory steps.

## TMTK Tools
This is the main addon of this repository. It sports the following features:
- **Export to FBX:** Export to FBX with the recommended settings for TMTK. No more worrying about which export settings to pick. This also can automatically execute the following animation fix.
- **Prepare an animation for export:** Subfreature of FBX export. Modifies the selected armature so you can export directly without going through the hassle of preparing the animation for export manually. After exporting, you can revert the changes with a single use of Blender's built-in Undo function. You do not need to run this function explicitly when using the addon's FBX exporter mentioned above. This function is meant for users who wish to apply the fix and then use another exporter.
- **Generate LODs:** Automatically create LODs L0-L5 for the selected objects. You'll still need to do manual work on the LODs for quality improvement, but the automatically generated LODs save you the effort of manually creating and renaming the copies.
- **Bone Weight Normalization:** This is a more precise version of Blender's built-in Normalize All feature for vertex group weights. This sometimes fixes TMTK's ugcArtifactNotFound and Too Many Influencers errors for animated items.
- **TMTK hints:** Open a panel with basic hints about the currently active object. Performs some of the pre-checks which are also done by the TMTK pipeline itself, such as verifying the correctness of LODs and checking the object size.

![TMTK Tools Menu Screenshot](https://tmtk.gohax.eu/screenshots/tmtktools.webp)

## TMTK Templates
This addon should originally be part of TMTK Tools but ended up as separate addon. By all accounts it should be in another repository, but it is so small that I just left it here for now. It adds a lot of Planet Coaster's common shapes to Blender's Mesh menu. Mostly wall and roof pieces.

- **Templates for common shapes:** Import templates for common shapes like walls and shop fronts directly from the 'Add Mesh' menu.
- **Toggle Grid-Mode:** All shapes come pre-setup for grid mode. You can change them to non-grid ('simple') mode with a single click.
- **LODs:** Most shapes come with pre-created LODs which are automatically addded by default.

*NOTE:* The templates themselves are not included in this repo. They are just FBX files, most of which were created by *Dada Poe*. The packaged addon including the template files is hosted at [the addon website](https://tmtk.gohax.eu/tmtktemplates).

![TMTK Templates Menu Screenshot](https://tmtk.gohax.eu/screenshots/tmtktemplates.webp)

## Installation
As usual, these Blender addons can be installed via the addon menu: EDIT -> Preferences -> Addons -> Install. Updating works the same, except that you might need to restart Blender for the changes to take effect.

## Blender Version Compatibility
I tested the addons with the major versions from Blender 2.80 to 4.0.2 - more recent versions usually also work. The addon does not work for versions 2.79 and older, as 2.80 introduced many breaking API changes.
