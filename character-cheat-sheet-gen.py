import jinja2
import json
import os
import sys

def check_chapter(data, chapter_id, chapter_map):
    from_ok = True
    if "from" in data:
        from_ok = chapter_map[data["from"]] <= chapter_id

    to_ok = True
    if "to" in data:
        to_ok = chapter_map[data["to"]] > chapter_id

    return from_ok and to_ok


def get_best_name(data, chapter_id, chapter_map):
    if "cape_names" in data:
        for name in data["cape_names"]:
            if not check_chapter(name, chapter_id, chapter_map):
                continue
            if name.get("not_main"):
                continue
            return name["value"]

    if "civilian_names" in data:
        for name in data["civilian_names"]:
            if not check_chapter(name, chapter_id, chapter_map):
                continue
            if name.get("not_main"):
                continue
            return name["value"]

    if "names" in data:
        for name in data["names"]:
            if not check_chapter(name, chapter_id, chapter_map):
                continue
            if name.get("not_main"):
                continue
            return name["value"]


def main():
    os.makedirs("out", exist_ok=True)
    environment = jinja2.Environment(
        loader=jinja2.FileSystemLoader("templates/")
    )
    environment.globals.update(check_chapter=check_chapter)
    environment.globals.update(get_best_name=get_best_name)
    template = environment.get_template("template.html")

    with open("character-cheat-sheet.json", "r", encoding="utf-8") as fd:
        data = json.load(fd)

        chapter_list = data["chapters"]
        character_objects = data["characters"]
        group_objects = data["groups"]
        association_objects = data["associations"]

        chapter_map = {
            chapter: i for i, chapter in enumerate(chapter_list)
        }
        chapter_filenames = {
            chapter: chapter.replace(" ", "-").lower() + ".html"
            for chapter in chapter_list
        }

        character_map = {}
        group_map = {}
        id_map = {}

        for i, character in enumerate(character_objects):
            character["id"] = "character-" + str(i)
            if "civilian_names" in character:
                for name in character["civilian_names"]:
                    assert name["value"] not in character_map
                    character_map[name["value"]] = i
            if "cape_names" in character:
                for name in character["cape_names"]:
                    assert name["value"] not in character_map
                    character_map[name["value"]] = i
            id_map["character-" + str(i)] = character

        for i, group in enumerate(group_objects):
            group["id"] = "group-" + str(i)
            if "names" in group:
                for name in group["names"]:
                    assert name["value"] not in group_map
                    group_map[name["value"]] = i
            id_map["group-" + str(i)] = group

        for association in association_objects:
            first, second = association["first"], association["second"]
            if first in character_map:
                first_id = "character-" + str(character_map[first])
                first_object = character_objects[character_map[first]]
            else:
                assert first in group_map
                first_id = "group-" + str(group_map[first])
                first_object = group_objects[group_map[first]]

            if second in character_map:
                second_id = "character-" + str(character_map[second])
                second_object = character_objects[character_map[second]]
            else:
                assert second in group_map
                second_id = "group-" + str(group_map[second])
                second_object = group_objects[group_map[second]]

            for obj, other_id, rel in [
                (first_object, second_id, association["relationship"]),
                (second_object, first_id, association["inv_relationship"])
            ]:
                if "associations" not in obj:
                    obj["associations"] = []
                new_assoc = {
                    "relationship": rel,
                    "other_id": other_id
                }
                if "from" in association:
                    new_assoc["from"] = association["from"]
                if "to" in association:
                    new_assoc["to"] = association["to"]
                if "to_soft" in association:
                    new_assoc["to_soft"] = association["to_soft"]
                obj["associations"] += [new_assoc]

        prev_chapter = None
        for chapter in chapter_list:
            chapter_id = chapter_map[chapter]
            chapter_filename = chapter_filenames[chapter]
            if chapter_id < len(chapter_list) - 1:
                next_chapter = chapter_list[chapter_id + 1]

            content = template.render(
                chapter=chapter,
                chapter_id=chapter_id,
                prev_chapter=prev_chapter,
                next_chapter=next_chapter,
                chapter_list=chapter_list,
                character_objects=character_objects,
                group_objects=group_objects,
                association_objects=association_objects,
                chapter_map=chapter_map,
                chapter_filenames=chapter_filenames,
                character_map=character_map,
                group_map=group_map,
                id_map=id_map,
                book="Worm"
            )
            with open(os.path.join("out", chapter_filename), "w", encoding="utf-8") as out:
                out.write(content)

            prev_chapter = chapter

if __name__ == "__main__":
    sys.exit(main())
