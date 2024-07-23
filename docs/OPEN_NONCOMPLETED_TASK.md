# 未完了タスクチェックフロー

この手順では、GitHub Projectsで未完了のタスクをチェックし、新しいIssueを作成するためのGitHub Actionsの設定方法を説明します。

## 事前準備

### 環境変数の設定

以下の環境変数をGitHubリポジトリのSecretsに設定する必要があります。

1. `TOKEN`: GitHub Personal Access Token
    - `TOKEN`は、`read:project`スコープ (クエリの場合) または `project`スコープ (クエリとミューテーションの場合) を持つトークンを使用します。このトークンは、ユーザーのpersonal access token (classic)でも、GitHub Appのインストール アクセス トークンでもかまいません。
    - Personal access tokenの作成について詳しくは、「[個人用アクセス トークンを管理する](https://docs.github.com/ja/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)」をご覧ください。
    - GitHub Appのインストール アクセス トークンの作成について詳しくは、「[GitHub アプリのインストール アクセス トークンの生成](https://docs.github.com/ja/developers/apps/authenticating-with-github-apps)」をご覧ください。

2. `USERNAME`: GitHubのユーザー名
3. `REPO_NAME`: リポジトリ名
4. `PROJECT_ID`: チェック対象のプロジェクトID

Secretsの設定方法:
1. リポジトリのページに移動します。
2. "Settings"タブをクリックします。
3. 左側のメニューから"Secrets and variables" > "Actions"を選択します。
4. "New repository secret"をクリックして、それぞれの環境変数を追加します。

### `PROJECT_ID`の確認方法

1. `curl`コマンドを使用して、プロジェクトIDを取得します。以下のコマンドをターミナルで実行します(TOKENとUSERNAMEは環境変数の設定で使用したものと同じものです):

    ```sh
    curl --request POST --url https://api.github.com/graphql --header 'Authorization: Bearer <TOKEN>' --data '{"query":"{user(login: \"<USERNAME>\") {projectsV2(first: 20) {nodes {id title}}}}"}'
    ```

2. 実行結果から対象プロジェクトのIDを確認し、`PROJECT_ID`として設定します。

## 使い方

### GitHub Actionsワークフローの作成

以下の内容で`.github/workflows/open-noncompleted-task.yml`ファイルを作成します。

```yaml
name: Daily Task Check

on:
  schedule:
    - cron: "0 11 * * *"  # 毎日20:00 JSTに実行
  workflow_dispatch:  # 手動トリガーを有効にする

jobs:
  check-tasks:
    runs-on: ubuntu-latest

    steps:
      - name: リポジトリをチェックアウト
        uses: actions/checkout@v2

      - name: Pythonをセットアップ
        uses: actions/setup-python@v2
        with:
          python-version: '3.x'

      - name: 依存関係をインストール
        run: pip install requests python-dotenv

      - name: タスクチェックスクリプトを実行
        env:
          TOKEN: ${{ secrets.TOKEN }}
          USERNAME: ${{ secrets.USERNAME }}
          REPO_NAME: ${{ secrets.REPO_NAME }}
          PROJECT_ID: ${{ secrets.PROJECT_ID }}
        run: python .github/scripts/check_tasks.py
```

### ワークフローの手動実行

1. GitHubリポジトリの"Actions"タブに移動します。
2. "Daily Task Check"ワークフローを選択します。
3. "Run workflow"ボタンをクリックして手動で実行します。

これで、指定されたプロジェクト内の未完了のタスクがチェックされ、新しいIssueが作成されます。