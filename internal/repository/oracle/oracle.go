package oracle

import (
	"context"
	"fmt"
	"strconv"

	"github.com/cyralinc/sidecar-failopen-healthcheck-aws/internal/config"
	"github.com/cyralinc/sidecar-failopen-healthcheck-aws/internal/keys"
	"github.com/cyralinc/sidecar-failopen-healthcheck-aws/internal/logging"
	"github.com/cyralinc/sidecar-failopen-healthcheck-aws/internal/repository"
	"github.com/cyralinc/sidecar-failopen-healthcheck-aws/internal/repository/genericsql"

	// Oracle DB driver
	_ "github.com/godror/godror"
)

const (
	OracleDriver = "godror"
)

type oracleRepository struct {
	// The majority of the repository.Repository functionality is delegated to
	// a generic SQL repository instance (genericSqlRepo).
	genericSqlRepo *genericsql.GenericSqlRepository
}

// *oracleRepository implements repository.Repository
var _ repository.Repository = (*oracleRepository)(nil)

func NewOracleRepository(_ context.Context, cfg config.RepoConfig) (repository.Repository, error) {

	connStr := fmt.Sprintf(
		`user="%s" password="%s" connectString="%s:%s/%s"`,
		cfg.User,
		cfg.Password,
		cfg.Host,
		strconv.Itoa(cfg.Port),
		cfg.Database,
	)

	logging.Info("instantiating oracle repository at %s:%s", cfg.Host, cfg.Port)
	sqlRepo, err := genericsql.NewGenericSqlRepository(cfg.RepoName, OracleDriver, cfg.Database, connStr)
	if err != nil {
		return nil, fmt.Errorf("could not instantiate generic sql repository: %w", err)
	}

	return &oracleRepository{genericSqlRepo: sqlRepo}, nil
}

// Ping verifies the connection to Oracle database used by this Repository.
// Normally we would just delegate to the Ping method implemented by
// genericsql.GenericSqlRepository. However, that implementation executes a
// 'SELECT 1' query to test for connectivity, and Oracle being Oracle, does not
// like this. So instead, we defer to the native Ping method implemented by the
// Oracle sql.DB driver.
func (repo *oracleRepository) Ping(ctx context.Context) error {
	return repo.genericSqlRepo.GetDb().PingContext(ctx)
}

func (repo *oracleRepository) Close() error {
	return repo.genericSqlRepo.Close()
}

func (repo *oracleRepository) Type() string {
	return keys.OracleRepoKey
}

func init() {
	repository.Register(keys.OracleRepoKey, NewOracleRepository)
}
