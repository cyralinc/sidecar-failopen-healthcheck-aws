// This package contains the general configuration for repositories
// and for the lambda in general
package config

import (
	"context"

	"github.com/cyralinc/sidecar-failopen-healthcheck-aws/internal/secrets"
	"github.com/spf13/viper"
)

// RepoConfig is the configuration for a repository, including
// connection information and metadata.
type RepoConfig struct {
	Host     string
	Port     int
	User     string
	Password string
	Database string
	RepoName string
	RepoType string
}

// LambdaConfig is the configuration for the lambda in general. This
// struct is to be used via the global Config function.
type LambdaConfig struct {
	NumberOfRetries int
	LogLevel        string
	StackName       string
	Sidecar         RepoConfig
	Repo            RepoConfig
}

func init() {
	// using prefix to get all environment variables starting with
	// "FAIL_OPEN" as configuration entries on viper
	viper.SetEnvPrefix("FAIL_OPEN")

	// sidecar location configuration
	viper.BindEnv("sidecar_port")
	viper.BindEnv("sidecar_host")

	// repository configuration
	viper.BindEnv("repo_type")
	viper.BindEnv("repo_host")
	viper.BindEnv("repo_port")
	viper.BindEnv("repo_name")
	viper.BindEnv("repo_database")
	viper.BindEnv("repo_secret")

	viper.BindEnv("n_retries") // number of retries on each healthcheck
	viper.BindEnv("log_level") // log level for the lambda

	viper.BindEnv("cf_stack_name") // name of the stack
}

var c *LambdaConfig

// Config returns the global configuration for the lambda function, initializing
// all values and recovering the secrets.
func Config() *LambdaConfig {
	if c == nil {
		sec, err := secrets.RepoSecretFromSecretsManager(context.Background(), viper.GetString("repo_secret"))
		if err != nil {
			panic(err)
		}

		c = &LambdaConfig{
			NumberOfRetries: viper.GetInt("n_retries"),
			LogLevel:        viper.GetString("log_level"),
			Repo: RepoConfig{
				Host:     viper.GetString("repo_host"),
				Port:     viper.GetInt("repo_port"),
				Database: viper.GetString("repo_database"),
				RepoType: viper.GetString("repo_type"),
				RepoName: viper.GetString("repo_name"),
				User:     sec.Username,
				Password: sec.Password,
			},
			Sidecar: RepoConfig{
				Host:     viper.GetString("sidecar_host"),
				Port:     viper.GetInt("sidecar_port"),
				Database: viper.GetString("repo_database"),
				RepoType: viper.GetString("repo_type"),
				RepoName: viper.GetString("repo_name"),
				User:     sec.Username,
				Password: sec.Password,
			},
		}
	}

	return c
}
