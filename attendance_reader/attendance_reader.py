import csv
from datetime import datetime
import pydantic
from enum import Enum, auto


class InMeetingActivity(pydantic.BaseModel):
    name: str
    email: str
    join_time: datetime
    leave_time: datetime
    duration: str
    role: str


class Participant(pydantic.BaseModel):
    email: str
    first_join: datetime
    last_leave: datetime
    in_meeting_duration: str
    participant_id: str
    role: str

class CSVConfig(pydantic.BaseModel):
    FILE_PATH: str
    ENCODING: str
    DELIMITER: str


class SectionHeading(Enum):
    START_TIME = auto()
    PARTICIPANTS = auto()
    MEETING_ACTIVITIES = auto()
    VIDEO_AND_AUDIO_CONSENT = auto()


class AttendanceConfig(pydantic.BaseModel):
    date_time_format: str
    section_headings_mapping: dict[str, SectionHeading]


class AttendanceReader:

    def __init__(
        self,
        csv_data: CSVConfig,
        attendance_config: AttendanceConfig,
    ):
        # store parameter variables
        self._CSV_CONFIG: CSVConfig = csv_data
        self._ATTENDANCE_CONFIG: AttendanceConfig = attendance_config

        # define variables to operate class
        self._csv_reader: csv.reader = None
        self._section_indexes: dict[SectionHeading, int] = {}

        # extract data
        self._init_csv_reader()
        self._extract_section_indexes()

    def _extract_section_indexes(self) -> None:

        for index, record in enumerate(self._csv_reader):

            # check if current line is a section heading
            section_name = record[0]

            if section_name in self._ATTENDANCE_CONFIG.section_headings_mapping.keys():

                section_id = self._ATTENDANCE_CONFIG.section_headings_mapping[
                    section_name
                ]
                self._section_indexes[section_id] = index + 2

    @property
    def start_time(self) -> datetime:
        return self._extract_start_time()

    @property
    def participants(self) -> list[Participant]:
        return self._extract_participants()

    @property
    def in_meeting_activities(self) -> list[InMeetingActivity]:
        return self._extract_in_meeting_activities()

    ####################################################
    #               Extraction Methods                 #
    ####################################################

    def _extract_start_time(self) -> datetime:
        start_time_index = self._section_indexes[SectionHeading.START_TIME]
        start_time_str = self._csv_reader[start_time_index][1]
        return self._convert_string_to_datetime(start_time_str)

    def _extract_participants(self) -> list[Participant]:
        participants: list[Participant] = []

        start_index = self._section_indexes[SectionHeading.PARTICIPANTS]
        end_index = self._section_indexes[SectionHeading.MEETING_ACTIVITIES] - 3

        for index in range(start_index, end_index):
            record = self._csv_reader[index]

            join_time = self._convert_string_to_datetime(record[1])
            leave_time = self._convert_string_to_datetime(record[2])
            in_meeting_duration = record[3]
            email = record[4]
            participant_id = record[5]
            role = record[6]

            participant = Participant(
                email=email,
                first_join=join_time,
                last_leave=leave_time,
                in_meeting_duration=in_meeting_duration,
                participant_id=participant_id,
                role=role,
            )

            participants.append(participant)

        return participants

    def _extract_in_meeting_activities(self) -> list[InMeetingActivity]:
        meeting_activities: list[InMeetingActivity] = []

        start_index = self._section_indexes[SectionHeading.MEETING_ACTIVITIES]
        end_index = self._section_indexes[SectionHeading.VIDEO_AND_AUDIO_CONSENT] - 3

        for index in range(start_index, end_index):
            record = self._csv_reader[index]

            name = record[0]
            join_time = self._convert_string_to_datetime(record[1])
            leave_time = self._convert_string_to_datetime(record[2])
            duration = record[3]
            email = record[4]
            role = record[5]

            activity = InMeetingActivity(
                name=name,
                email=email,
                join_time=join_time,
                leave_time=leave_time,
                duration=duration,
                role=role,
            )

            meeting_activities.append(activity)

        return meeting_activities

    def _convert_string_to_datetime(self, date_time_str: str) -> datetime:
        return datetime.strptime(
            date_time_str, self._ATTENDANCE_CONFIG.date_time_format
        )

    def _init_csv_reader(self) -> None:
        with open(
            self._CSV_CONFIG.FILE_PATH,
            mode="r",
            newline="",
            encoding=self._CSV_CONFIG.ENCODING,
        ) as file:
            self._csv_reader = csv.reader(file, delimiter=self._CSV_CONFIG.DELIMITER)


if __name__ == "__main__":

    attendance_config = AttendanceConfig(
        date_time_format="%m/%d/%y, %I:%M:%S %p",
        section_headings_mapping={
            "Start time": SectionHeading.START_TIME,
            "2. Participants": SectionHeading.PARTICIPANTS,
            "3. In-Meeting Activities": SectionHeading.MEETING_ACTIVITIES,
            "4. Explicit Audio and Video Consent Information": SectionHeading.VIDEO_AND_AUDIO_CONSENT,
        },
    )
