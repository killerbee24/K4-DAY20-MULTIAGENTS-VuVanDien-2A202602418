---
name: protect-original-files
description: Use this when a task forbids modifying certain files but allows creating or modifying others.
---
1. At the start, identify which files must not be modified (e.g., tests/, original data files).
2. Create a list of approved files to edit and new files to create.
3. Before editing any file, confirm it is on the approved list. If unsure, create a new file instead.
4. After implementation, verify no protected files were changed:
   - For version-controlled repos, run `git status` and check the diff.
   - For non-versioned work, compare file modification timestamps or checksums against the original.
5. If a protected file was modified, restore it from the original and reapply changes to an approved file.
6. Completion check: No protected files appear in the diff or modification log.
