from uuid import uuid4

import numpy as np
import pytest

from prefect.server.schemas.actions import (
    MAX_FLOW_DESCRIPTION_LENGTH,
    DeploymentCreate,
    DeploymentUpdate,
    FlowCreate,
    FlowRunCreate,
    FlowUpdate,
)


@pytest.mark.parametrize(
    "test_flow, expected_dict",
    [
        (
            {"name": "valid_flow", "description": "short_valid_description"},
            {"name": "valid_flow", "description": "short_valid_description"},
        ),
        pytest.param(
            {
                "name": "invalid_flow",
                "description": "long invalid description" * MAX_FLOW_DESCRIPTION_LENGTH,
            },
            None,
            marks=pytest.mark.xfail,
        ),
    ],
)
class TestFlowCreate:
    def test_flow_create_validates_description(self, test_flow, expected_dict):
        fc = FlowCreate(name=test_flow["name"], description=test_flow["description"])
        assert fc.name == test_flow["name"]
        assert fc.description == test_flow["description"]


@pytest.mark.parametrize(
    "test_flow, expected_dict",
    [
        ({"description": "flow_description"}, {"description": "flow_description"}),
        pytest.param(
            {
                "description": "long invalid description" * MAX_FLOW_DESCRIPTION_LENGTH,
            },
            None,
            marks=pytest.mark.xfail,
        ),
    ],
)
class TestFlowUpdate:
    def test_flow_update_validates_description(self, test_flow, expected_dict):
        fu = FlowUpdate(description=test_flow["description"])
        assert fu.description == expected_dict["description"]


@pytest.mark.parametrize(
    "test_params,expected_dict",
    [
        ({"param": 1}, {"param": 1}),
        ({"param": "1"}, {"param": "1"}),
        ({"param": {1: 2}}, {"param": {"1": 2}}),
        (
            {"df": {"col": {0: "1"}}},
            {"df": {"col": {"0": "1"}}},
        ),  # Example of serialized dataframe parameter with int key
        (
            {"df": {"col": {0: np.float64(1.0)}}},
            {"df": {"col": {"0": 1.0}}},
        ),  # Example of serialized dataframe parameter with numpy value
    ],
)
class TestFlowRunCreate:
    def test_dict_json_compatible_succeeds_with_parameters(
        self, test_params, expected_dict
    ):
        frc = FlowRunCreate(flow_id=uuid4(), flow_version="0.1", parameters=test_params)
        res = frc.dict(json_compatible=True)
        assert res["parameters"] == expected_dict


class TestDeploymentCreate:
    def test_create_with_worker_pool_queue_id_warns(self):
        with pytest.warns(
            UserWarning,
            match=(
                "`worker_pool_queue_id` is no longer supported for creating "
                "deployments. Please use `work_pool_name` and "
                "`work_queue_name` instead."
            ),
        ):
            deployment_create = DeploymentCreate(
                **dict(name="test-deployment", worker_pool_queue_id=uuid4())
            )

        assert getattr(deployment_create, "worker_pool_queue_id", 0) == 0

    @pytest.mark.parametrize(
        "kwargs",
        [
            ({"worker_pool_queue_name": "test-worker-pool-queue"}),
            ({"work_pool_queue_name": "test-work-pool-queue"}),
            ({"worker_pool_name": "test-worker-pool"}),
        ],
    )
    def test_create_with_worker_pool_name_warns(self, kwargs):
        with pytest.warns(
            UserWarning,
            match=(
                "`worker_pool_name`, `worker_pool_queue_name`, and "
                "`work_pool_name` are"
                "no longer supported for creating "
                "deployments. Please use `work_pool_name` and "
                "`work_queue_name` instead."
            ),
        ):
            deployment_create = DeploymentCreate(
                **dict(name="test-deployment", **kwargs)
            )

        for key in kwargs.keys():
            assert getattr(deployment_create, key, 0) == 0


class TestDeploymentUpdate:
    def test_update_with_worker_pool_queue_id_warns(self):
        with pytest.warns(
            UserWarning,
            match=(
                "`worker_pool_queue_id` is no longer supported for updating "
                "deployments. Please use `work_pool_name` and "
                "`work_queue_name` instead."
            ),
        ):
            deployment_update = DeploymentUpdate(**dict(worker_pool_queue_id=uuid4()))

        assert getattr(deployment_update, "worker_pool_queue_id", 0) == 0

    @pytest.mark.parametrize(
        "kwargs",
        [
            ({"worker_pool_queue_name": "test-worker-pool-queue"}),
            ({"work_pool_queue_name": "test-work-pool-queue"}),
            ({"worker_pool_name": "test-worker-pool"}),
        ],
    )
    def test_update_with_worker_pool_name_warns(self, kwargs):
        with pytest.warns(
            UserWarning,
            match=(
                "`worker_pool_name`, `worker_pool_queue_name`, and "
                "`work_pool_name` are"
                "no longer supported for creating "
                "deployments. Please use `work_pool_name` and "
                "`work_queue_name` instead."
            ),
        ):
            deployment_update = DeploymentCreate(**kwargs)

        for key in kwargs.keys():
            assert getattr(deployment_update, key, 0) == 0
