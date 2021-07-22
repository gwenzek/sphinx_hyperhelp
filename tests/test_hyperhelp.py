from pathlib import Path

from sphinx_hyperhelp import HelpFile, HelpIndex, HelpTopic


def test_prune():
    index = HelpIndex("SphinxTest", "nice tests", Path("."))
    index.help_files["keep_all.txt"] = HelpFile()
    index.help_files["keep_all.txt"].topics.append(
        HelpTopic("keep_all", aliases=["keep_all_bis", "keep_all_ter"])
    )

    index.help_files["keep_main.txt"] = HelpFile()
    index.help_files["keep_main.txt"].topics.append(
        HelpTopic("keep_main", aliases=["keep_main_bis", "keep_main_ter"])
    )
    index.help_files["keep_alias.txt"] = HelpFile()
    index.help_files["keep_alias.txt"].topics.append(
        HelpTopic("keep_alias", aliases=["keep_alias_bis", "keep_alias_ter"])
    )
    index.help_files["drop_all.txt"] = HelpFile()
    index.help_files["drop_all.txt"].topics.append(
        HelpTopic("drop_all", aliases=["drop_all_bis", "drop_all_ter"])
    )

    keep_topics = {
        "keep_all",
        "keep_all_bis",
        "keep_all_ter",
        "keep_main",
        "keep_alias_ter",
    }
    index = index.prune(keep_topics=keep_topics)

    index_topics = set()
    for hf in index.help_files.values():
        for help_topic in hf.topics:
            index_topics.add(help_topic.topic)
            index_topics.update(help_topic.aliases)

    assert set(index_topics) == keep_topics
    assert index.help_files["drop_all.txt"].topics == []
