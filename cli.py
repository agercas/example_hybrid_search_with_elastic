import os

import typer

from src.api.search import Search

app = typer.Typer()


@app.command()
def reindex(file_path: str = typer.Argument(..., help="Path to the JSON file containing documents to be indexed.")):
    """
    Regenerates the Elasticsearch index by creating a new index
    and inserting documents from the specified JSON file.
    """
    if not os.path.exists(file_path):
        typer.echo(f"The file {file_path} does not exist.")
        raise typer.Abort()

    search_instance = Search()
    response = search_instance.reindex(file_path=file_path)

    typer.echo(f"Index regeneration completed. {len(response['items'])} documents added.")


if __name__ == "__main__":
    app()
