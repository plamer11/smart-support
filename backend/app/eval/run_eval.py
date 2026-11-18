
from ..config import settings
from ..graph.nodes import faq_node


QUESTIONS = [
    {"question": "你们支持几天无理由退货？", "ground_truth": "签收后7天内可无理由退货，商品需保持完好。", "expect_section": "退货退款政策"},
    {"question": "定制商品能退吗？", "ground_truth": "定制商品不支持无理由退货，质量问题可返厂维修或重做。", "expect_section": "退货退款政策"},
    {"question": "买家具运费怎么算？", "ground_truth": "大件家具满 999 元包邮，未满收取 99 元基础运费。", "expect_section": "配送说明"},
    {"question": "发票多久能开好？", "ground_truth": "电子发票签收后 24 小时内开具并发送到邮箱。", "expect_section": "发票与售后"},
    {"question": "积分怎么获得，能干嘛用？", "ground_truth": "消费 1 元得 1 积分，100 积分抵 1 元，生日当月双倍。", "expect_section": "会员与积分"},
]


def collect_predictions():

    from ..rag.retriever import get_retriever

    retriever = get_retriever()
    predictions = []
    for item in QUESTIONS:
        docs = retriever.invoke(item["question"])
        result = faq_node({"question": item["question"], "history": []})
        predictions.append({
            "question": item["question"],
            "answer": result["answer"],
            "contexts": [d.page_content for d in docs],
            "ground_truth": item["ground_truth"],
            "retrieved_sections": [d.metadata.get("section", "") for d in docs],
            "expect_section": item["expect_section"],
        })
    return predictions


def evaluate():
    try:
        from datasets import Dataset
        from langchain_openai import ChatOpenAI
        from ragas import evaluate as ragas_evaluate
        from ragas.llms import LangchainLLMWrapper
    except ImportError:
        print("请先安装评估依赖：pip install ragas datasets")
        return

    predictions = collect_predictions()
    ds = Dataset.from_list(predictions)

    judge_llm = LangchainLLMWrapper(
        ChatOpenAI(
            model=settings.llm_model,
            api_key=settings.api_key,
            base_url=settings.llm_base_url,
        )
    )
    result = ragas_evaluate(
        dataset=ds,
        llm=judge_llm,
        metrics=["faithfulness", "answer_relevancy", "context_precision"],
    )
    print("ragas 评估结果：")
    print(result)


if __name__ == "__main__":
    evaluate()
