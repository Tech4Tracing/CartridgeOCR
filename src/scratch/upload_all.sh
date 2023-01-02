#!/bin/bash
cd  /mnt/c/GitHub/CartridgeOCR/data/extracted_headstamps_deduped_grouped/
for g in 1 2 3 4 5 6; do
    python ~/CartridgeOCR/src/scratch/import_collection.py --root-url https://annotations.tech4tracing.net --collection_name Group_${g} --cookie "session=.eJwlzkGuAjEIANC7dO0ktEALXsZAgWjiyslf_Xh3Tdy95ftvt3rleW_XsueZl3Z7RLu26A5VFMWdvwyy4nIcQrFUHBcDIixl4wgLZdUFWynRN9DIHIyM4qPmNFFZBTJxbtxoY3Tgoa5uSzOoQ8QWDQXrCzKn-G7fyN-Zr98m59wMaod39YNKxmHgeRgzdfKBa2d7fwDxjTic.Y42WTA.wIj8T0lgmVwp6Fc9hCRwi7B0cEg; HttpOnly; Path=/" --delete-existing ./group_${g}
done