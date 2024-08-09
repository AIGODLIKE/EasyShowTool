### v0.2.1

**New Feature**

+ improve multiple selection
    + shift + click to add selection
    + ctrl + click to remove selection
    + option: select all corner/one corner to select a layer

**Fix**

+ error when press x to remove when no layer

### v0.2.0

> 2024/8/3

**New Feature**

+ Initial support for multiple selection
    + Transform
        + Move selected g
        + Rotate selected r
        + Scale selected s
    + Alignment & Distribution
        + Left/right/top/bottom alignment
        + Horizontal center/vertical center alignment
        + Horizontal/Vertical Distribution
    + Color
        + Change Selected Color
        + Change Selected opacity
        + New UI
    + Delete
        + Delete selected object

+ Scale/Rotate Improvement
    + Use bounding box center instead of stroke pivot(which work bad on some object)

+ Blender svg icon
    + bounding stroke remove is more accurate now

### v0.1.3

> 2024/7/17

**Fix**

+ ensure builtin font when the addon is not enable in exist file
+ delete error in new view modal
+ enable error in background mode
+ some debug info will not show in release mode

**Change**

+ view draw no longer needs click to show, instead, it will show when switch to the tool
+ Now the addon can be installed as an Extension

### v0.1.2

> 2024.7.15

**Fix**

+ Without a 3D view import icon, errors will no longer be reported
+ Alt copy error when there is no active item object
+ Error reporting when there is no active layer

### v0.1.1

> 2024.7.14

**New Feature**

+ Add object
    + add property thickness
    + add property opacity

+ Add Modal operator G to move
    + right click cancel
    + left click confirm

+ new palette system (fix error report when first use)
    + provide preset color
    + provide socket color
    + use popover panel to show

**Fix**

+ fix error report when first use
+ alt + click to copy move will change active object
+ no 3d view import icon will no longer report error

### v0.1.0

> 2024.7.12

First Version