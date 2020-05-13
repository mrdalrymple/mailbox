This file will contain ideas or questions that are not flushed out as stories yet.

# Questions

## General

## Storage
Question: When adding an item to the storage, do we actually want to have to specify an ID?
 - What is that ID really?
 - Could it just be it's first label, and we don't have to store these
packaged under the hood using that ID?
 - What if users uploaded something to the wrong ID and
want to move it?  They could just use remove and add.
 - Note: I'm going to go down one route, but I think this should have another look at (or evolve over time).

Question: Do we want there to be a local cache of store information?
 - Should this be something handled via the plugin library?
  - Company/vendor specific?
  - Consumer default? (is probably as-is since everything stored locally)
 - Should there then be storage remotes?
  - Do we then push/pull database updates?
  - Do we make this like git remote?


## API

- Should have a flag / setting to be able to choose whether the external libraries get pulled into the local .mb directory or the system .mb directory
- Should pull external libraries into heirarchy of repo name then folders per version/branch


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

## Local Database Directory

What do we call .mb/?
- It will contain things like .mb/inbox, .mb/outbox, .mb/env, etc.

It's like a local database.  No one would want to override this stuff right?
What does git call their .git folder?

The reason this is important is for having a convenient name to refer to this, for speaking, documentation, and variable names.

# Labels

## Custom labels
Do we want a "special labels" section in the db.yml?
- woud be a dictionary (key/value pairs) of label name and label value.
- automatically added to label queries
- not able to be deleted via the CLI?
- Example - layout_hash: a23d91f...
- This might be something orgs want to automatically add
- Do we do this on package creation?
  - What about when package already created by org makes a new special/custom label type?  How to propogate that to all?

# TODOs

These should be user stories, but I don't know if I want to put in that effort right now.
So either, write stories for these TODOs, or just do them:

- Add ability to remove a package from the store
- Add ability to cleanup current working directory
 - clean all of $cwd/.mb?
 - clean just $cwd/.mb/storage?
 - If $cwd/.mb is empty, why not just remove whole folder on clean?
 - Possible command: `mb clean` (or does it need to be `mb build clean`?)
- Explore the situation where someone runs `mb store get LUA/acdef` multiple times
 - What if the local package is corrupt, i.e. someone deleted some files?
  - Maybe current solution is fairly good, where we just keep re-extracting zip... just need to do a clean beforehand..
  - What about large zips!?... this works well for small, but not optimized for very large packages.
