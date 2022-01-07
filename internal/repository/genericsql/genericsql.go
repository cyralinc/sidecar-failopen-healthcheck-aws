package genericsql

import (
	"context"
	"database/sql"
	"fmt"

	"github.com/cyralinc/sidecar-failopen-healthcheck-aws/internal/logging"
	"github.com/cyralinc/sidecar-failopen-healthcheck-aws/internal/repository"
)

const (
	PingQuery = "SELECT 1"
)

/*
GenericSqlRepository is an implementation of repository.Repository that
works for a subset of ANSI SQL compatible databases. In addition to the
standard repository.Repository methods, it also exposes some SQL-specific
functionality, which may be useful for other repository.Repository
implementations.
*/
type GenericSqlRepository struct {
	repoName string
	repoType string
	database string
	db       *sql.DB
}

// *GenericSqlRepository implements repository.Repository
var _ repository.Repository = (*GenericSqlRepository)(nil)

/*
NewGenericSqlRepository is the constructor for the GenericSqlRepository type.
Note that it returns a pointer to GenericSqlRepository rather than
repository.Repository. This is intentional, as the GenericSqlRepository type
exposes additional functionality on top of the repository.Repository
interface. If the caller is not concerned with this additional functionality,
they are free to assign to the return value to repository.Repository
*/
func NewGenericSqlRepository(repoName, repoType, database, connStr string) (*GenericSqlRepository, error) {
	db, err := getDbHandle(repoType, connStr)
	if err != nil {
		return nil, fmt.Errorf("error retrieving DB handle for repo type %s: %w", repoType, err)
	}
	return &GenericSqlRepository{
		repoName: repoName,
		repoType: repoType,
		database: database,
		db:       db,
	}, nil
}

func (repo *GenericSqlRepository) Ping(ctx context.Context) error {
	logging.Debug("pinging repo")
	rows, err := repo.db.QueryContext(ctx, PingQuery)
	if err != nil {
		return err
	}
	defer rows.Close()
	return nil
}

// GetDb is a getter for the repository's sql.DB handle.
func (repo *GenericSqlRepository) GetDb() *sql.DB {
	return repo.db
}

func (repo *GenericSqlRepository) Close() error {
	return repo.db.Close()
}

func getDbHandle(repoType, connStr string) (*sql.DB, error) {
	db, err := sql.Open(repoType, connStr)
	if err != nil {
		return nil, err
	}

	return db, nil
}
