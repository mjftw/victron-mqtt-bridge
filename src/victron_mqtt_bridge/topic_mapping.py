from collections.abc import Mapping

# Maps a relative Victron topic path (the segment after N/<serial>/, e.g.
# "battery/0/Soc") to the full topic to publish on the downstream broker.
type TopicMapping = Mapping[str, str]
