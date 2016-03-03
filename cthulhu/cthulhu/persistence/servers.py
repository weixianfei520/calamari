

from sqlalchemy import Column, Text, Integer, ForeignKey, Boolean, DateTime
from calamari_common.db.base import Base


class Server(Base):
    """
    A table of the servers seen by ServerMonitor, lazily updated
    """
    __tablename__ = 'cthulhu_server'

    id = Column(Integer, autoincrement=True, primary_key=True)

    # FQDN is not primary key because it can change if a server
    # was previously known to use by hostname and subsequently
    # it becomes known to use by full FQDN.
    fqdn = Column(Text, primary_key=False)
    hostname = Column(Text)
    managed = Column(Boolean)
    last_contact = Column(DateTime(timezone=True))
    boot_time = Column(DateTime(timezone=True))
    ceph_version = Column(Text)

    def __repr__(self):
        return "<Server %s>" % self.fqdn


class Service(Base):
    """
    A table of the ceph services seen by ServerMonitor, usually
    each one is associated with a Server, lazily updated.
    """
    __tablename__ = 'cthulhu_server_service'

    fsid = Column(Text, primary_key=True)
    service_type = Column(Text, primary_key=True)
    # mon name or OSD id (as string)
    service_id = Column(Text, primary_key=True)

    # Whether the service process is running
    running = Column(Boolean)
    # Any status metadata (mon_status) reported, as json string
    status = Column(Text)

    server = Column(Integer, ForeignKey("cthulhu_server.id"), nullable=True)
