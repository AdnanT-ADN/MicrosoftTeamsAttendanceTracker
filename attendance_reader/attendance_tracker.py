from attendance_reader import (
    Participant,
    SessionData,
    CSVConfig,
    SectionHeading,
    AttendanceConfig,
    AttendanceReader,
    InMeetingActivity,
)
from datetime import datetime
import pydantic
from typing import Optional


class AttendanceTracker:

    def __init__(
        self,
        attendance_csv_path: str,
        csv_encoding="uft-8",
        csv_delimiter=",",
    ) -> None:
        self._attendance_reader: Optional[AttendanceReader] = None

        self._init_attendance_reader(attendance_csv_path, csv_encoding, csv_delimiter)

    def _init_attendance_reader(
        self, csv_file_path: str, csv_encoding: str, csv_delimiter: str
    ):
        CSV_CONFIG = CSVConfig(
            FILE_PATH=csv_file_path, ENCODING=csv_encoding, DELIMITER=csv_delimiter
        )

        ATTENDANCE_CONFIG = AttendanceConfig(
            date_time_format="%m/%d/%y, %I:%M:%S %p",
            section_headings_mapping={
                "Start time": SectionHeading.START_TIME,
                "2. Participants": SectionHeading.PARTICIPANTS,
                "3. In-Meeting Activities": SectionHeading.MEETING_ACTIVITIES,
                "4. Explicit Audio and Video Consent Information": SectionHeading.VIDEO_AND_AUDIO_CONSENT,
            },
        )

        self._attendance_reader = AttendanceReader(CSV_CONFIG, ATTENDANCE_CONFIG)

    def get_qualified_participants(
        self,
        session_start_time: datetime,
        session_end_time: datetime,
        minimum_attendance_percentage: float,
    ) -> list[str]:
        qualified_participants: list[str] = []

        participant_time_mapping: dict[str, int] = {}

        minimum_minutes_threshold = int(
            ((session_end_time - session_start_time).total_seconds() // 60)
            * minimum_attendance_percentage
        )

        for activity in self._attendance_reader.in_meeting_activities:
            if activity.email not in participant_time_mapping:
                participant_time_mapping[activity.email] = 0

            start_time = (
                0
                if activity.join_time >= session_end_time
                else max(session_start_time, activity.leave_time)
            )

            end_time = min(session_end_time, activity.join_time)

            participant_time_mapping[activity.email] += (
                0
                if start_time == 0
                else int((end_time - start_time).total_seconds() // 60)
            )

        for email, total_time in participant_time_mapping.items():
            if total_time >= minimum_minutes_threshold:
                qualified_participants.append(email)

        return qualified_participants

    def generate_qualified_participants_file(
        self,
        output_file: str,
        session_start_time: datetime,
        session_end_time: datetime,
        minimum_attendance_percentage: float,
    ) -> None:

        qualified_participants = self.get_qualified_participants(
            session_start_time, session_end_time, minimum_attendance_percentage
        )
        with open(output_file, "w") as file:
            file.write(",".join(qualified_participants))


if __name__ == "__main__":
    pass
