import os
import re
import requests

BASEROW_TOKEN = os.environ["BASEROW_TOKEN"]
TABLE_ID = os.environ["TABLE_ID"]

BASE_URL = "https://api.baserow.io"

HEADERS = {
    "Authorization": f"Token {BASEROW_TOKEN}",
    "Content-Type": "application/json",
}


def get_rows():
    rows = []
    page = 1
    size = 100

    while True:
        url = (
            f"{BASE_URL}/api/database/rows/table/"
            f"{TABLE_ID}/"
            f"?user_field_names=true"
            f"&page={page}"
            f"&size={size}"
        )

        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()

        data = response.json()
        batch = data.get("results", [])

        rows.extend(batch)

        if len(batch) < size:
            break

        page += 1

    return rows


def extract_youtube_id(url):
    patterns = [
        r"(?:youtube\.com/watch\?v=)([^&\s]+)",
        r"(?:youtu\.be/)([^?\s]+)",
        r"(?:youtube\.com/shorts/)([^?\s]+)",
        r"(?:youtube\.com/embed/)([^?\s]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)

        if match:
            return match.group(1)

    return None


def upload_from_url(image_url):
    url = f"{BASE_URL}/api/user-files/upload-via-url/"

    response = requests.post(
        url,
        headers=HEADERS,
        json={
            "url": image_url
        },
    )

    response.raise_for_status()

    return response.json()


def update_row(row_id, image_url, filename):
    url = (
        f"{BASE_URL}/api/database/rows/table/"
        f"{TABLE_ID}/{row_id}/"
        f"?user_field_names=true"
    )

    response = requests.patch(
        url,
        headers=HEADERS,
        json={
            "ImageUrl": image_url,
            "Thumbnail": [
                {
                    "name": filename
                }
            ],
        },
    )

    response.raise_for_status()


def main():
    rows = get_rows()

    print(f"Total de linhas encontradas: {len(rows)}")

    for row in rows:
        row_id = row["id"]

        thumbnail = row.get("Thumbnail")
        youtube_url = row.get("Url")

        # Só processa linhas sem Thumbnail
        if thumbnail:
            continue

        if not youtube_url:
            print(f"[{row_id}] Sem URL")
            continue

        video_id = extract_youtube_id(youtube_url)

        if not video_id:
            print(f"[{row_id}] URL não reconhecida como YouTube: {youtube_url}")
            continue

        image_url = (
            f"https://img.youtube.com/vi/"
            f"{video_id}/maxresdefault.jpg"
        )

        print(f"[{row_id}] YouTube: {video_id}")
        print(f"[{row_id}] Imagem: {image_url}")

        try:
            uploaded = upload_from_url(image_url)
            filename = uploaded["name"]

            update_row(
                row_id,
                image_url,
                filename
            )

            print(f"[{row_id}] ✓ ImageUrl e Thumbnail atualizados")

        except Exception as error:
            print(f"[{row_id}] ✗ Erro: {error}")


if __name__ == "__main__":
    main()
