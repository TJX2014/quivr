import tempfile
from typing import List

from fastapi import UploadFile
from langchain.prompts import HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain_community.chat_models import ChatLiteLLM
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from logger import get_logger
from modules.assistant.dto.inputs import InputAssistant
from modules.assistant.dto.outputs import (
    AssistantOutput,
    InputFile,
    Inputs,
    OutputBrain,
    OutputEmail,
    Outputs,
)
from modules.assistant.ito.ito import ITO
from modules.user.entity.user_identity import UserIdentity

logger = get_logger(__name__)


class DifferenceAssistant(ITO):

    def __init__(
        self,
        input: InputAssistant,
        files: List[UploadFile] = None,
        current_user: UserIdentity = None,
        **kwargs,
    ):
        super().__init__(
            input=input,
            files=files,
            current_user=current_user,
            **kwargs,
        )

    def check_input(self):
        if not self.files:
            raise ValueError("No file was uploaded")
        if len(self.files) != 2:
            raise ValueError("Only two files can be uploaded")
        if not self.input.inputs.files:
            raise ValueError("No files key were given in the input")
        if len(self.input.inputs.files) != 2:
            raise ValueError("Only two files can be uploaded")
        if not self.input.inputs.files[0].key == "doc_1":
            raise ValueError("The key of the first file should be doc_1")
        if not self.input.inputs.files[1].key == "doc_2":
            raise ValueError("The key of the second file should be doc_2")
        if not self.input.inputs.files[0].value:
            raise ValueError("No file was uploaded")
        if not (
            self.input.outputs.brain.activated or self.input.outputs.email.activated
        ):
            raise ValueError("No output was selected")
        return True

    async def process_assistant(self):

        document_1 = self.files[0]
        document_2 = self.files[1]

        document_1_tmp = tempfile.NamedTemporaryFile(delete=False)
        document_2_tmp = tempfile.NamedTemporaryFile(delete=False)

        document_1_tmp.write(document_1.file.read())
        document_2_tmp.write(document_2.file.read())

        document_1_loader = UnstructuredPDFLoader(document_1_tmp.name)
        document_2_loader = UnstructuredPDFLoader(document_2_tmp.name)

        document_1_tmp.close()
        document_2_tmp.close()

        document_1_loaded = document_1_loader.load()
        document_2_loaded = document_2_loader.load()

        logger.error(f"Document 1: {document_1_loaded[0].page_content}")
        logger.error(f"Document 2: {document_2_loaded[0].page_content}")

        llm = ChatLiteLLM(model="gpt-3.5-turbo")

        human_prompt = """Given the following two documents, find the difference between them:

        Document 1:
        {document_1}
        Document 2:
        {document_2}
        Difference:
        """
        CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(human_prompt)

        system_message_template = """
        You are an expert in finding the difference between two documents. You look deeply into what makes the two documents different and provide a detailed analysis.
        """

        ANSWER_PROMPT = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(system_message_template),
                HumanMessagePromptTemplate.from_template(human_prompt),
            ]
        )

        final_inputs = {
            "document_1": document_1_loaded[0].page_content,
            "document_2": document_2_loaded[0].page_content,
        }

        output_parser = StrOutputParser()

        chain = ANSWER_PROMPT | llm | output_parser
        result = chain.invoke(final_inputs)

        return result


def difference_inputs():
    output = AssistantOutput(
        name="difference",
        description="Finds the difference between two sets of documents",
        tags=["new"],
        input_description="Two documents to compare",
        output_description="The difference between the two documents",
        icon_url="https://quivr-cms.s3.eu-west-3.amazonaws.com/assistant_summary_434446a2aa.png",
        inputs=Inputs(
            files=[
                InputFile(
                    key="doc_1",
                    allowed_extensions=["pdf"],
                    required=True,
                    description="The first document to compare",
                ),
                InputFile(
                    key="doc_2",
                    allowed_extensions=["pdf"],
                    required=True,
                    description="The second document to compare",
                ),
            ]
        ),
        outputs=Outputs(
            brain=OutputBrain(
                required=True,
                description="The brain to which upload the document",
                type="uuid",
            ),
            email=OutputEmail(
                required=True,
                description="Send the document by email",
                type="str",
            ),
        ),
    )
    return output
