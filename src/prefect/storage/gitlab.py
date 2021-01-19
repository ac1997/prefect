from typing import TYPE_CHECKING, Any, Dict
from urllib.parse import quote_plus

from prefect.storage import Storage
from prefect.utilities.storage import extract_flow_from_file

if TYPE_CHECKING:
    from prefect.core.flow import Flow


class GitLab(Storage):
    """
    GitLab storage class. This class represents the Storage interface for Flows stored
    in `.py` files in a GitLab repository.

    This class represents a mapping of flow name to file paths contained in the git repo,
    meaning that all flow files should be pushed independently. A typical workflow using
    this storage type might look like the following:

    - Compose flow `.py` file where flow has GitLab storage:

    ```python
    flow = Flow("my-flow")
    # Can also use `repo="123456"`
    flow.storage = GitLab(repo="my/repo", path="/flows/flow.py", ref="my-branch")
    ```

    - Push this `flow.py` file to the `my/repo` repository under `/flows/flow.py`.

    - Call `prefect register flow -f flow.py` to register this flow with GitLab storage.

    Args:
        - repo (str): the project path (i.e., 'namespace/project') or ID
        - host (str, optional): If using Gitlab server, the server host. If not specified, defaults
            to Gitlab cloud.
        - path (str, optional): a path pointing to a flow file in the repo
        - ref (str, optional): a commit SHA-1 value or branch name
        - **kwargs (Any, optional): any additional `Storage` initialization options
    """

    def __init__(
        self,
        repo: str,
        host: str = None,
        path: str = None,
        ref: str = None,
        **kwargs: Any,
    ) -> None:
        self.flows = dict()  # type: Dict[str, str]
        self._flows = dict()  # type: Dict[str, "Flow"]
        self.repo = repo
        self.host = host
        self.path = path
        self.ref = ref

        super().__init__(**kwargs)

    def get_flow(self, flow_name: str) -> "Flow":
        """
        Given a flow name within this Storage object, load and return the Flow.

        Args:
            - flow_name (str): the name of the flow to return.

        Returns:
            - Flow: the requested flow
        """
        if flow_name not in self.flows:
            raise ValueError("Flow is not contained in this Storage")
        flow_location = self.flows[flow_name]

        ref = self.ref or "master"

        from gitlab.exceptions import GitlabAuthenticationError, GitlabGetError

        try:
            project = self._gitlab_client.projects.get(quote_plus(self.repo))
            contents = project.files.get(file_path=flow_location, ref=ref)
        except GitlabAuthenticationError:
            self.logger.error(
                "Unable to authenticate Gitlab account. Please check your credentials."
            )
            raise
        except GitlabGetError:
            self.logger.error(
                f"Error retrieving file contents at {flow_location} in {self.repo}@{ref}. "
                "Ensure the project and file exist."
            )
            raise

        return extract_flow_from_file(
            file_contents=contents.decode(), flow_name=flow_name
        )

    def add_flow(self, flow: "Flow") -> str:
        """
        Method for storing a new flow as bytes in the local filesytem.

        Args:
            - flow (Flow): a Prefect Flow to add

        Returns:
            - str: the location of the added flow in the repo

        Raises:
            - ValueError: if a flow with the same name is already contained in this storage
        """
        if flow.name in self:
            raise ValueError(
                'Name conflict: Flow with the name "{}" is already present in this storage.'.format(
                    flow.name
                )
            )

        self.flows[flow.name] = self.path  # type: ignore
        self._flows[flow.name] = flow
        return self.path  # type: ignore

    def build(self) -> "Storage":
        """
        Build the GitLab storage object and run basic healthchecks. Due to this object
        supporting file based storage no files are committed to the repository during
        this step. Instead, all files should be committed independently.

        Returns:
            - Storage: a GitLab object that contains information about how and where
                each flow is stored
        """
        self.run_basic_healthchecks()

        return self

    def __contains__(self, obj: Any) -> bool:
        """
        Method for determining whether an object is contained within this storage.
        """
        if not isinstance(obj, str):
            return False
        return obj in self.flows

    @property
    def _gitlab_client(self):  # type: ignore
        from prefect.utilities.git import get_gitlab_client

        return get_gitlab_client(host=self.host)
