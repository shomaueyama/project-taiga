from typing import Any

MATERIAL_CATALOG: dict[str, dict[str, str | None]] = {
    "MAT-PC-BROTHER": {
        "title": "兄作成PC課題",
        "provider": "Project Taiga",
        "type": "assignment",
        "url": None,
    },
    "MAT-ETYPE": {
        "title": "e-typing",
        "provider": "イータイピング",
        "type": "practice",
        "url": "https://www.e-typing.ne.jp/",
    },
    "MAT-PAIZA-LINUX": {
        "title": "paizaラーニング Linux入門",
        "provider": "paiza",
        "type": "course",
        "url": "https://paiza.jp/works",
    },
    "MAT-MAN": {
        "title": "Linux man pages",
        "provider": "man7.org",
        "type": "reference",
        "url": "https://man7.org/linux/man-pages/dir_section_1.html",
    },
    "MAT-GIT-SARU": {
        "title": "サル先生のGit入門",
        "provider": "Backlog",
        "type": "guide",
        "url": "https://backlog.com/ja/git-tutorial/",
    },
    "MAT-GIT-OFFICIAL": {
        "title": "Git公式ドキュメント",
        "provider": "Git",
        "type": "reference",
        "url": "https://git-scm.com/doc",
    },
    "MAT-PAIZA-C": {
        "title": "paizaラーニング C言語入門",
        "provider": "paiza",
        "type": "course",
        "url": "https://paiza.jp/works",
    },
    "MAT-CS50JP": {
        "title": "CS50x",
        "provider": "Harvard CS50",
        "type": "course",
        "url": "https://cs50.harvard.edu/x/",
    },
    "MAT-KITAMI": {
        "title": "きたみ式イラストIT塾 基本情報技術者",
        "provider": "技術評論社",
        "type": "book",
        "url": None,
    },
    "MAT-FE-WEB": {
        "title": "基本情報技術者過去問道場",
        "provider": "過去問道場",
        "type": "practice",
        "url": "https://www.fe-siken.com/fekakomon.php",
    },
    "MAT-IPA": {
        "title": "IPA 基本情報技術者試験",
        "provider": "IPA",
        "type": "official",
        "url": "https://www.ipa.go.jp/shiken/kubun/fe.html",
    },
}


def materials_for_task(material_ids: list[Any], goal: str | None) -> list[dict[str, Any]]:
    materials: list[dict[str, Any]] = []
    for index, raw_id in enumerate(material_ids):
        material_id = str(raw_id)
        catalog = MATERIAL_CATALOG.get(material_id)
        if catalog is None:
            materials.append(
                {
                    "id": material_id,
                    "title": material_id,
                    "provider": "Unknown",
                    "type": "reference",
                    "url": None,
                    "required": index == 0,
                    "purpose": "concept" if index == 0 else "reference",
                    "learningObjective": goal,
                }
            )
            continue
        materials.append(
            {
                "id": material_id,
                **catalog,
                "required": index == 0,
                "purpose": "concept" if index == 0 else "reference",
                "learningObjective": goal,
            }
        )
    return materials
