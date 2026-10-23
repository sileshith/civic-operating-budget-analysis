# Publishing guide

Suggested name: **civic-operating-budget-analysis**

Description: Excel and SQLite portfolio project for budget variance reporting, five-year operating forecasts and a two-year spending proposal using synthetic data.

Topics: `budget-analysis`, `excel`, `sql`, `sqlite`, `financial-analysis`, `portfolio`, `synthetic-data`.

Featured artifact: `reports/Civic_Operating_Budget_Analysis_Report.pdf`.

Public repository: https://github.com/sileshith/civic-operating-budget-analysis

This guide retains the commands for publishing a separate copy or maintaining future releases.

## Publish with Git

After creating your chosen empty GitHub repository, run from the project folder:

```sh
git init -b main
git add .
git commit -m "Add synthetic Excel and SQL budget analysis portfolio"
git remote add origin YOUR_REPOSITORY_URL
git push -u origin main
```

Replace `YOUR_REPOSITORY_URL` with the actual URL. These commands are instructions; they were not executed. The included workflow runs checks and rebuilds the PDF after publication.

Read the report, practice the workbook and retain the synthetic-data and AI-assistance disclosures. After model changes, regenerate SQL outputs, run tests, align the workbook, rebuild the PDF and visually inspect the release. Update the report/citation dates and README reference values when publishing a new snapshot.

Do not add a hosted-CI success badge until the workflow actually passes. The project has no course submissions, private contacts, credentials or employer records.
