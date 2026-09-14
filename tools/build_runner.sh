#!/usr/bin/env sh
# Rebuild runtime/java/workbook-runner.jar from tools/runner/workbook/Runner.java.
# Needs a JDK (javac and jar); the class files target Java 8 for CheerpJ.
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
BUILD="$ROOT/.build/runner"
rm -rf "$BUILD" && mkdir -p "$BUILD"
javac --release 8 -Xlint:-options -cp "$ROOT/runtime/java/ecj.jar" -d "$BUILD" "$ROOT/tools/runner/workbook/Runner.java"
jar --create --date=2000-01-01T00:00:00Z --file "$ROOT/runtime/java/workbook-runner.jar" -C "$BUILD" .
echo "built runtime/java/workbook-runner.jar"
