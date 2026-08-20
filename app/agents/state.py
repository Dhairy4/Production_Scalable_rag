from typing import TypedDict, List, Annotated
import operator


class AgentState(TypedDict):
    # using the add operator so, message appends rather replace

    messages: Annotated[List[str], operator.add]
    current_query : str
    documents : List[str]
    plan: List[str]
    status : str
    final_answer : str


    