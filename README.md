## Intro 'Easy Show Tool'

**Easy Show Tool** is a blender addon that allow you to add complex and amazing note in node editor. It is quick, fast
and easy to use.

The notes you created will be **stored in the blend file**, so it is easy to share with others who has not installed
this addon, which helps them to understand your wonderful nodes jobs

## Feature

1. text annotation

    + double click to open text editor

2. complex annotation

    + create from multiple types
        + text
            + custom font
        + object
            + gpencil object
            + mesh object
        + blender icon
    + tool
      support local/global transform
        + move
        + rotate
            + snap angle support
        + scale
            + uniform scale
            + non-uniform scale
            + center scale
            + from corner / edge center
            + `F` to flip
        + color
            + preset color (compatible with socket color)

## Keymap

| Function                              | Shortcut                  | Description                               |
|---------------------------------------|---------------------------|-------------------------------------------|
| Set Active                            | click                     | Set the current active layer              |
| Add                                   | double_click              | Add amazing notes in the node editor      |
| Drop Color                            | C                         | Set the color of the current active layer |
| Move                                  | click_drag                | Drag without pressing Ctrl or Shift       |
| Copy Move                             | ALT + click_drag          | Drag while pressing Alt                   |
| Scale Center,  Both Side / Keep Radio | CTRL + SHIFT + click_drag | Drag while pressing Ctrl and Shift        |
| Scale Center                          | CTRL + left click_drag    | Drag while pressing Ctrl                  |
| Scale Both Side / Keep Radio          | SHIFT + left click_drag   | Drag while pressing Shift                 |
| Delete                                | X                         | Delete selected content                   |
| Flip Horizontal                       | F                         | Flip scale vector                         |
| Flip Vertical                         | SHIFT + F                 | Flip scale vector                         |