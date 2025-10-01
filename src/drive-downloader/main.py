import logging

from utils import sink
from alidaparse.output import OutDatasetFactory, OutModelFactory
from alidaparse.input import InParamFactory
import tempfile
import gdown

def download(root_path,file_name,google_id,extension,to):
    gdown.download(output=f"{root_path}/{file_name}{extension}",id=google_id, quiet=False)
    gdown.extractall(f"{tmpdirname}/{file_name}{extension}",to)

if __name__ == "__main__":
    is_model = InParamFactory.from_cli(name="is_model",
                                  param_type=bool,
                                  required=False
                                  ).param_value
    is_dataset = InParamFactory.from_cli(name="is_dataset",
                                  param_type=bool,
                                  required=False
                                  ).param_value
    id = InParamFactory.from_cli(name="google_drive_id",
                                 param_type=str,
                                 required=True).param_value

    extension = InParamFactory.from_cli(name="extension",
                                    param_type=str,
                                    required=True
                                    ).param_value

    logging.warning(is_dataset)
    logging.warning(is_model)
    logging.warning(id)
    logging.warning(extension)
    if not (is_model ^ is_dataset):
        raise RuntimeError("Either is_model or is_dataset must be specified")

    if is_model:
        output= OutModelFactory.from_cli()
        output_name = output.model
    else:
        output = OutDatasetFactory.from_cli()
        output_name = output.dataset

    with tempfile.TemporaryDirectory() as tmpdirname:
        download(root_path=tmpdirname,
                 file_name="data",
                 google_id=id,
                 extension=extension,
                 to=f"{tmpdirname}/extracted"
        )
        sink(
            local_folder=f"{tmpdirname}/extracted",
            minio_url=output.minio_url,
            bucket_name=output.minio_bucket,
            minio_path=output_name,
            secret_key=output.secret_key,
            access_key=output.access_key,
        )
