-- Link quality-check results to the pipeline execution that
-- produced them, and classify each check by type/severity so
-- results are queryable structured records rather than just
-- pass/fail log lines.

BEGIN;

ALTER TABLE retail.ingestion_quality_results
    ADD COLUMN IF NOT EXISTS pipeline_run_id UUID,
    ADD COLUMN IF NOT EXISTS check_type VARCHAR(50)
        NOT NULL DEFAULT 'COMPLETENESS',
    ADD COLUMN IF NOT EXISTS severity VARCHAR(20)
        NOT NULL DEFAULT 'ERROR';

ALTER TABLE retail.ingestion_quality_results
    ALTER COLUMN check_type DROP DEFAULT,
    ALTER COLUMN severity DROP DEFAULT;

ALTER TABLE retail.ingestion_quality_results
    ADD CONSTRAINT chk_quality_result_check_type
        CHECK (
            check_type IN (
                'COMPLETENESS',
                'UNIQUENESS',
                'REFERENTIAL_INTEGRITY',
                'FINANCIAL_CONSISTENCY'
            )
        ),
    ADD CONSTRAINT chk_quality_result_severity
        CHECK (
            severity IN (
                'ERROR',
                'WARNING'
            )
        ),
    ADD CONSTRAINT fk_quality_results_pipeline_run
        FOREIGN KEY (pipeline_run_id)
        REFERENCES analytics.pipeline_runs(pipeline_run_id);

CREATE INDEX IF NOT EXISTS
    idx_quality_results_pipeline_run
ON retail.ingestion_quality_results(pipeline_run_id);

COMMIT;
