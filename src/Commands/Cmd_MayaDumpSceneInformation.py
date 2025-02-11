from contextlib import suppress

with suppress(ModuleNotFoundError):
    import maya.standalone
    maya.standalone.initialize(name="python")

    import maya.cmds as cmds


import Core

logger = Core.get_logger()


from CommandBase import CommandBase


class Cmd_MayaDumpSceneInformation(CommandBase):
    label = "Sample - Maya: Dump Scene Information"
    tooltip = "Dump scene information"
    ui_class = "CmdUI_FileCollector"

    def run(self, data={}):
        target_files = data["target_files"]

        for target_file in target_files:
            logger.info("process: {0}".format(target_file))
            cmds.file(force=True, newFile=True)
            cmds.file(target_file, f=True, open=True)

            for o in cmds.ls():
                logger.info("Object: {0}".format(o))
