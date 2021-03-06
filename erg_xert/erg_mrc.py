import logging
from typing import List

from erg_xert.file_type import FileType
from erg_xert.workout import WorkoutStep


class ErgMrcFile:
    logger = logging.getLogger('ErgMrcFile')

    def is_erg_mrc_file(filename: str):
        try:
            file_type = FileType.from_filename(filename)
        except TypeError:
            return False

        return file_type in [FileType.ERG, FileType.MRC]

    def load_from_file(filename: str):
        logger = ErgMrcFile.logger
        file_type = FileType.from_filename(filename)
        ftpMode = file_type == FileType.MRC
        ftp = 100
        with open(filename, 'r') as f:
            lines = f.read().splitlines()

        line = lines.pop(0)
        # Parse the header section
        while line != "[COURSE DATA]":
            if file_type == FileType.ERG and line.startswith("FTP"):
                ftpMode = True
                ftp = int(line.split("=")[1].strip())
            if line.startswith("DESCRIPTION"):
                workout_name = line.split("=")[1].strip()
            line = lines.pop(0)

        # Get the workout data from the COURSE DATA section
        workout_data: List[WorkoutStep] = []

        if ftpMode:
            xert_type = "relative_ftp"
        else:
            xert_type = "absolute"

        while lines:
            line1 = lines.pop(0)
            # Stop when we get to the end of the data
            if line1 == "[END COURSE DATA]":
                break;
            line2 = lines.pop(0)
            line1 = line1.split()
            line2 = line2.split()
            power1 = line1[1]
            power2 = line2[1]
            if power1 != power2:
                logger.error(
                    "Error: Xert workout steps cannot do power ramps, so pairs of lines must have identical power")
                logger.error("First line power: " + power1 + ", second line power: " + power2)
                logger.error("Skipping interval")
                continue;
            else:
                if ftpMode:
                    value = int(100 * float(power1) / ftp)
                else:
                    value = int(power1)
            duration = float(line2[0]) - float(line1[0])
            mins = int(duration)
            secs = round((duration - mins) * 60)
            workout_data.append(WorkoutStep(value, mins, secs, xert_type))
        return workout_name, workout_data
