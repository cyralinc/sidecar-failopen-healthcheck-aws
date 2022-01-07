package main

import (
	"context"
	"github.com/aws/aws-lambda-go/lambda"
	"github.com/cyralinc/sidecar-failopen-healthcheck-aws/internal/failopen"
)

// main could be a simple call `lambda.Start(<handler>)`. However, to avoid
// parsing the config every time the lambda is invoked, we build the config
// outside the lambda handler.
func main() {
	lambda.Start(
		func(ctx context.Context) error {
			return failopen.Run(ctx)
		},
	)
}
