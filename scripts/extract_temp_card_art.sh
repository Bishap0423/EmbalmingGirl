#!/bin/sh
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
source_pdf="$root/Embalming_Girl_(Rules-English).pdf"
output="$root/apps/web/public/assets/temporary/cards"
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

command -v pdfimages >/dev/null
command -v magick >/dev/null
test -f "$source_pdf"
mkdir -p "$output"

pdfimages -j "$source_pdf" "$work/img"

convert_card() {
  number=$1
  name=$2
  magick "$work/img-$number.jpg" -strip -quality 82 "$output/$name.webp"
}

convert_card 028 alien
convert_card 030 student_council_president
convert_card 032 infected
convert_card 034 criminal
convert_card 036 accomplice
convert_card 038 class_representative
convert_card 040 prodigy
convert_card 042 disciplinary_committee
convert_card 044 health_committee
convert_card 046 lady
convert_card 048 library_committee
convert_card 050 newspaper_club
convert_card 052 go_home_club

echo "Temporary card art extracted to $output"
