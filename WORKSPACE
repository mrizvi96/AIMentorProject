# AI Mentor Bazel Workspace

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

# Rules for OCI (Docker) images
http_archive(
    name = "rules_oci",
    sha256 = "176e601d21d1151efd88b6b027a24e782493c5d623d8c6211c7767f306d655c8",
    strip_prefix = "rules_oci-1.2.0",
    url = "https://github.com/bazel-contrib/rules_oci/releases/download/v1.2.0/rules_oci-v1.2.0.tar.gz",
)

load("@rules_oci//oci:dependencies.bzl", "rules_oci_dependencies")
rules_oci_dependencies()

load("@rules_oci//oci:repositories.bzl", "LATEST_CRANE_VERSION", "oci_register_toolchains")
oci_register_toolchains(
    name = "oci",
    crane_version = LATEST_CRANE_VERSION,
)

# Rules for packaging
http_archive(
    name = "rules_pkg",
    sha256 = "8f9ee2dc10c1ae514ee599a8b42ed99fa262b757058f65ad3c384289ff70c4b8",
    urls = [
        "https://mirror.bazel.build/github.com/bazelbuild/rules_pkg/releases/download/0.9.1/rules_pkg-0.9.1.tar.gz",
        "https://github.com/bazelbuild/rules_pkg/releases/download/0.9.1/rules_pkg-0.9.1.tar.gz",
    ],
)

load("@rules_pkg//pkg:deps.bzl", "rules_pkg_dependencies")
rules_pkg_dependencies()

# Pull base image
load("@rules_oci//oci:pull.bzl", "oci_pull")

oci_pull(
    name = "runpod_pytorch",
    image = "runpod/pytorch",
    tag = "1.0.2-cu1281-torch280-ubuntu2404",
    digest = "sha256:your_digest_here",  # You'll need to get this
)
