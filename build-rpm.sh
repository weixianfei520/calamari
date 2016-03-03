# adapted from 1.1's jenkins build script, aiming for self-reliance
cd ..
WORKSPACE=$(pwd)

RPMBUILD=${WORKSPACE}/rpmbuild
SRC=${WORKSPACE}/calamari
rm -rf ${RPMBUILD}

# Build tarball
(cd ${SRC}; make dist)
TARNAME="calamari-server_*tar.gz"

# Set up build area
mkdir -p ${RPMBUILD}/{SOURCES,SRPMS,SPECS,RPMS,BUILD}
cp -a ${TARNAME} ${RPMBUILD}/SOURCES
cp -a calamari/calamari.spec ${RPMBUILD}/SPECS

# set VERSION and REVISION so make doesn't try to get it from git
# (as it'll be off in the BUILD/ dir, which isn't a git repo)

eval $(cd ${SRC}; ./get-versions.sh -r)
export VERSION
export REVISION

# Build RPMs
cd ${RPMBUILD}
rpmbuild -bb --define "_topdir ${RPMBUILD}" --define "_unpackaged_files_terminate_build 0" --define "version ${VERSION}" --define "revision ${REVISION}" SPECS/calamari.spec

# XXX who signs when?

## Sign the rpms
#for RPMPKG in `find ${REPO} -name "*.rpm"`
#do
#    ${CEPH_BUILD_DIR}/rpm-autosign.exp --define "_gpg_name ${KEYID}" ${RPMPKG}
#done
