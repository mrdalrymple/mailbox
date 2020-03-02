# Store - ls with invalid ref (package_hash)
Run command `mb store ls REF` where a REF.package_hash does not exist REF(storage_id, ???)
Result is wrong, says: "More than one result for: $REF.package_hash", should say: "Unknown package '$REF.package_hash"

# Store - ls with invalid ref (storage_id)
Run command `mb store ls REF` where a REF.storage_id does not exist REF(???, ???)
Result is wrong, it's an uncaught exception, should say: "Unknown storage_id '$REF.storage_id"
