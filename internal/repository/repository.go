package repository

import (
	"context"

	"github.com/cyralinc/sidecar-failopen-healthcheck-aws/internal/config"
)

type Repository interface {
	Ping(context.Context) error
	Close() error
	Type() string
}

var factory map[string]RepositoryHandlerInstantiator

type RepositoryHandlerInstantiator func(context.Context, config.RepoConfig) (Repository, error)

func Register(key string, instantiator RepositoryHandlerInstantiator) {

	if factory == nil {
		factory = map[string]RepositoryHandlerInstantiator{}
	}

	factory[key] = instantiator
}

func Recover(key string) RepositoryHandlerInstantiator {

	return factory[key]
}
