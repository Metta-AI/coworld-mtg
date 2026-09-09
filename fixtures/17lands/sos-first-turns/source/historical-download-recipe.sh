#!/bin/bash
set -uo pipefail
cd "$(dirname "$0")/inputs"

fetch() {
  local name="$1" url="$2" out="$3"
  if [ -s "$out" ]; then echo "SKIP $name (exists)"; return 0; fi
  if curl -sfL --retry 3 -o "$out.part" "$url"; then
    mv "$out.part" "$out"
    echo "OK $name $(shasum -a 256 "$out" | cut -d' ' -f1) $(du -h "$out" | cut -f1)"
  else
    rm -f "$out.part"
    echo "FAIL $name $url"
  fi
}

bulk=$(curl -sfL https://api.scryfall.com/bulk-data)
oracle_uri=$(echo "$bulk" | python3 -c "import json,sys; d=json.load(sys.stdin); print(next(x['download_uri'] for x in d['data'] if x['type']=='oracle_cards'))")
rulings_uri=$(echo "$bulk" | python3 -c "import json,sys; d=json.load(sys.stdin); print(next(x['download_uri'] for x in d['data'] if x['type']=='rulings'))")
echo "oracle_uri=$oracle_uri"
echo "rulings_uri=$rulings_uri"

fetch scryfall-oracle "$oracle_uri" scryfall-oracle.json
fetch scryfall-rulings "$rulings_uri" scryfall-rulings.json
fetch mtgjson-sos "https://mtgjson.com/api/v5/SOS.json" mtgjson-SOS.json
fetch 17lands-game "https://17lands-public.s3.amazonaws.com/analysis_data/game_data/game_data_public.SOS.PremierDraft.csv.gz" 17lands-game.SOS.PremierDraft.csv.gz
fetch 17lands-replay "https://17lands-public.s3.amazonaws.com/analysis_data/replay_data/replay_data_public.SOS.PremierDraft.csv.gz" 17lands-replay.SOS.PremierDraft.csv.gz
echo "DOWNLOADS_DONE"
