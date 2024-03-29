#!/bin/sh

echo "Integration Tests for Jenkins"
echo "============================="
echo ""
echo "👉 This is the standard output."
echo "This is the standard error. 👈" 1>&2
echo ""

echo "Tests commencing in…"
for i in 5 4 3 2 1; do
    echo "…$i"
    sleep 1
done

docker-compose \
    --ansi never \
    --profile int-registry-batch-loader \
    --project-name registry \
    --file ${WORKSPACE}/docker/docker-compose.yml \
    run \
    --rm \
    --no-TTY \
    testrail-reporting-test \
    </dev/null
status=$?

echo ""
echo "Tests exited with status: $status"
echo "Thanks for running them! 👋"
exit $status
