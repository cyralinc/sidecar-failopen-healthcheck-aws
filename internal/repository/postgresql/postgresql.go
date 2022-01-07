package postgresql

import (
	"context"
	"fmt"
	"strconv"

	"github.com/cyralinc/sidecar-failopen-healthcheck-aws/internal/config"
	"github.com/cyralinc/sidecar-failopen-healthcheck-aws/internal/keys"
	"github.com/cyralinc/sidecar-failopen-healthcheck-aws/internal/logging"
	"github.com/cyralinc/sidecar-failopen-healthcheck-aws/internal/repository"
	"github.com/cyralinc/sidecar-failopen-healthcheck-aws/internal/repository/genericsql"

	// Postgresql DB driver
	_ "github.com/lib/pq"
)

// PostgreSQL is the name registered by the DB driver.
const PostgreSQL = "postgres"

type postgresqlRepository struct {
	// The majority of the repository.Repository functionality is delegated to
	// a generic SQL repository instance (genericSqlRepo).
	genericSqlRepo *genericsql.GenericSqlRepository
}

// *postgresqlRepository implements repository.Repository
var _ repository.Repository = (*postgresqlRepository)(nil)

func NewPostgresqlRepository(_ context.Context, cfg config.RepoConfig) (repository.Repository, error) {

	connStr := fmt.Sprintf(
		"postgresql://%s:%s@%s:%s/%s",
		cfg.User,
		cfg.Password,
		cfg.Host,
		strconv.Itoa(cfg.Port),
		cfg.Database,
	)

	logging.Info("instantiating postgres repository at %s:%s", cfg.Host, cfg.Port)

	sqlRepo, err := genericsql.NewGenericSqlRepository(cfg.RepoName, PostgreSQL, cfg.Database, connStr)
	if err != nil {
		return nil, fmt.Errorf("could not instantiate generic sql repository: %w", err)
	}

	return &postgresqlRepository{genericSqlRepo: sqlRepo}, nil
}

func (repo *postgresqlRepository) Ping(ctx context.Context) error {
	return repo.genericSqlRepo.Ping(ctx)
}

func (repo *postgresqlRepository) Close() error {
	return repo.genericSqlRepo.Close()
}

func (repo *postgresqlRepository) Type() string {
	return keys.PGRepoKey
}

func init() {
	repository.Register(keys.PGRepoKey, NewPostgresqlRepository)
}
