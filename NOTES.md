This file will contain ideas or questions that are not flushed out as stories yet.

# Questions

Question: When adding an item to the storage, do we actually want to have to specify an ID?
 - What is that ID really?
 - Could it just be it's first label, and we don't have to store these
packaged under the hood using that ID?
 - What if users uploaded something to the wrong ID and
want to move it?  They could just use remove and add.
 - Note: I'm going to go down one route, but I think this should have another look at (or evolve over time).






# CLI

## Storage

#list all my current packckages
manage my packages
- what I have
- what versions of those things/their labels
- add a new label
- remove a label
- view the contents of a package

mb storage list
mb storage label LUA acdef
mb storage label LUA/acdef

> mb storage 
# output of all package names (todo: what if there are tons of packages!?)

> mb storage LUA
# output all of the versions/(sub packages AKA the actual zips)
# - question: should I call these "sub packages" (which are actually packages) "versions"
#  or "references" and references HAVE a version (what does having a version mean?)?

> mb storage LUA/acdef
# currently: outputing the labels
# additionaly do: show the root contents of that sub package/version.
# question: do I show both? the labels and the contents, or just show the contents, and they must specify --label to view the labels for that subpackage.




> mb storage LUA/acdef/2de/Bin/


mb storage LUA/acdef/2de/Bin/ --rmlabel 

