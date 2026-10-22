# Adding photos

Use only photos supplied by the project owner or explicitly approved after a rights review. Public availability is not permission. This system does not download photos or determine legal permissions automatically.

1. Verify the exact image, photographer, and license at the original source. Confirm website use, commercial use if applicable, attribution, derivatives, and any share-alike obligations. Check separate privacy, publicity, trademark, and property permissions where relevant. Do not use unclear rights, prohibited uses, or edits forbidden by a license. Record evidence of permission and the owner's explicit approval. Giving credit alone is not permission.
2. Keep the original and permission/license evidence in your own archive, outside the public repository. Never commit private emails, personal information, or full-resolution originals. Add a non-sensitive evidence reference in the record below. For direct submissions, have the photographer supply written permission and an approved public credit/permission statement URL; do not invent a license or publish a private email.
3. Install Pillow on your editing computer (`python3 -m pip install Pillow`). Optimize a local file:

   ```sh
   python3 scripts/prepare_photo.py /path/to/approved-original.jpg assets/photos/bridal-veil-falls.webp
   ```

   The script never downloads or overwrites images. It applies EXIF orientation, limits both dimensions to 1600px, strips embedded metadata including GPS, and writes a WebP of at most 400,000 bytes. Color appearance and compression should be visually reviewed. Resizing, format conversion, metadata removal, and any crop or color edits must be allowed by the permission/license and recorded as modifications. Keep the original attribution and rights notices in the metadata record even though embedded metadata is removed.
4. In `data/hikes.json`, replace the hike's `"photo": null` with a record like this **only after verification and approval**. Example text is a template, not a license grant:

   ```json
   "photo": {
     "src": "assets/photos/bridal-veil-falls.webp",
     "alt": "Describe what this particular photograph shows",
     "title": "The photographer's image title",
     "photographer": "Exact approved credit, including required copyright notice",
     "source_url": "https://example.com/original-photo",
     "license": "Exact license name/version or written-permission label",
     "license_url": "https://example.com/license-or-public-permission-statement",
     "modifications": "Resized and converted to WebP; embedded metadata removed; no crop",
     "rights_evidence": "Non-sensitive archive reference and review date; owner approval reference",
     "approved": true
   }
   ```

   Do not set `approved` until the owner has supplied the photo for use or explicitly approved the image after its license was verified. This flag records a human decision; the build cannot verify legal rights. Include any required attribution-party names or copyright notices in `photographer`, retain the work's title, link to the actual source and license, and describe every modification. If the license requires wording or obligations the current fields cannot satisfy, extend the attribution before publishing. Do not substitute an unrelated license URL. For public-domain or CC0 work, still record creator/source where available and link to evidence of that status.
5. Run `python3 scripts/build.py`, `python3 scripts/check.py`, and `python3 scripts/test_photos.py`. Review the actual photo, alternative text, visible attribution, and Photo Credits page on mobile and desktop. Commit the WebP, metadata, and generated pages together. Cloudflare serves these static files with no additional production dependency or build step.

The image retains its natural aspect ratio, has explicit dimensions to reduce layout shift, and uses lazy loading and asynchronous decoding. Listing cards use the primary photo when available and link to the guide for full credits; otherwise they retain illustrations. Photographs and their attribution appear together on hike detail pages. Add an optional `caption` to explain the view. For multiple photos, add an `additional_photos` array of complete photo records alongside the primary `photo`; every entry is validated and credited on Photo Credits. Use `photo: null` to keep the illustration placeholder. Credit entries are generated automatically from active photo records; removing a record removes its credit. Archive the record with the permission evidence before removal.

## Existing homepage image

`assets/BryceCanyon.webp` is the existing owner-supplied homepage image (2048 × 1078, approximately 512KB). The site owner confirmed on October 21, 2026 (America/Denver) that they personally took the photo and explicitly requested deployment. This records permission for its use on Take a Hike Utah, not a public reuse license. Photo Credits identifies the photographer as the Take a Hike Utah site owner; copyright remains with the photographer. The file is owner-supplied, with responsive display sizing/cropping; earlier editing history is unknown. No Creative Commons or other public license is inferred. No replacement or additional photograph has been sourced. The build caps this existing hero at 2048px and 600,000 bytes; new hike photos have the stricter 1600px/400,000-byte limit.

## Personal hike photos added October 22, 2026

The owner supplied JennysCanyon.jpg, SunsetPoint_Bryce.jpg, and SunrisePoint_Bryce.jpg in Hikes.zip and explicitly authorized cropping/conversion and site placement. The three local WebP derivatives are credited to the site owner, with all rights reserved and permission limited to this site. No public reuse license is inferred. Crops use a 16:10 frame and preserve the main landscape; no color edits were made. GPS and embedded metadata were removed. Original files are not committed. Jenny’s Canyon is captioned as the surrounding landscape rather than the slot interior. Both Bryce images are shown on the Sunset-to-Sunrise guide.
