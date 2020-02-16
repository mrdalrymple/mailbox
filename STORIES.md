# Key
- UR = User Requirement
- DR = Developement Requirement

# Personas

## Bob
- developer
- makes changes when dependencies update

# Stories

## Manage Storage

### View Current
As a user, I want to be able to get a listing of the packages in storage, with their ID

### Add New
As a user, I want to be able to add a package to the storage (assign it an ID?), so that I can
support newer tools by my application
- [UR] Can supply a zip or a root path
  - If root path: zip up contents, zip file is hash of contents
- [UR] If the package already exists, I should be informed of this, and the information about the package

- [DR] I want the internal format to be <storage_root>/<package ID>/<unique/identifying>/<package contents>
  - unique/identifying should be hash of the contents
  - should be a config file under <package id> called "properties"
  - should package contents be a zip file? (yes let's start with this)
- [DR] User needs to supply an ID
  - TODO: Rethink this? What if they want to assign an ID back later, I guess how would they know

- FUTURE: Maybe make requirement that zips get saved in a db store
  - would need to create lookup logic
  - this would save space if user uploads same zip to a different package id

