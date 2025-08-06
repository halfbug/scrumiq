from fastapi import APIRouter, HTTPException, Query, Request, status
from typing import List, Dict, Any
from utilities.types.tokenz import Tokenz
from datetime import datetime
from pydantic import BaseModel
from collections import defaultdict

router = APIRouter()

# Initialize the TokenzModel with your MongoDB URI and database name


@router.get("/tokens/{user_id}", response_description="Get all tokens by user ID", response_model=List[Tokenz])
def get_tokens_by_user_id(user_id: str, request: Request):
    print("user_id", user_id)
    tokens = request.app.database["tokenz"].find({"user_id": user_id})
    print("tokens", tokens)
    tokens_list = list(tokens)
    for token in tokens_list:
        token["_id"] = str(token["_id"])
    print("tokens_list", tokens_list)
    if tokens_list:
        return tokens_list
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No tokens found for user ID {user_id}")

@router.get("/tokens/range/{user_id}", response_description="Get tokens by date range and average usage", response_model=Dict[str, Any])
def get_tokens_by_date_range(user_id: str, start_date: str, end_date: str, request: Request):
    start_date = datetime.fromisoformat(start_date)
    end_date = datetime.fromisoformat(end_date)
    
    tokens = request.app.database["tokenz"].find({
        "user_id": user_id,
        "update_time": {"$gte": start_date, "$lte": end_date}
    })
    
    tokens_list = list(tokens)
    for token in tokens_list:
        token["_id"] = str(token["_id"])
    
    if not tokens_list:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No tokens found for user ID {user_id} in the given date range")
    
    total_input_tokens = sum(token["input_tokens"] for token in tokens_list)
    total_output_tokens = sum(token["output_tokens"] for token in tokens_list)
    total_tokens = sum(token["total_tokens"] for token in tokens_list)
    question_types = set(token.get("question_type", "unknown") for token in tokens_list)
    
    
    average_usage = {
        "average_input_tokens": total_input_tokens / len(tokens_list),
        "average_output_tokens": total_output_tokens / len(tokens_list),
        "average_total_tokens": total_tokens / len(tokens_list)
    }
    
    return {
        "tokens": tokens_list,
        "average_usage": average_usage,
        "question_types": list(question_types)
    }
class TokenAverages(BaseModel):
    input_token_average: float
    output_token_average: float
    total_token_average: float

class QuestionData(BaseModel):
    question_type: str
    total_requests: int
    model_4o_mini: TokenAverages
    gemini_1_5_flash: TokenAverages

class OverallAverages(BaseModel):
    model_4o_mini: TokenAverages
    gemini_1_5_flash: TokenAverages

@router.get("/tokens/averages/{user_id}", response_model=Dict[str, Any])
def get_token_averages(request: Request, user_id: str):
    collection = request.app.database["tokenz"]
    print("user_id", user_id)
    
    pipeline = [
        # {
        #     "$match": {"user_id": user_id}  
        # },
        {
            "$group": {
                "_id": {
                    "question_type": {
                        "$cond": {
                            "if": {"$eq": ["$question_type", None]},
                            "then": "unknown",
                            "else": "$question_type",
                        }
                    },
                    "model_name": "$model_name"
                },
                "total_input_tokens": {"$sum": "$input_tokens"},
                "total_output_tokens": {"$sum": "$output_tokens"},
                "total_tokens": {"$sum": "$total_tokens"},
                "count": {"$sum": 1}
            }
        },
        {
            "$project": {
                "_id": 0,
                "question_type": "$_id.question_type",
                "model_name": "$_id.model_name",
                "input_token_average": {"$divide": ["$total_input_tokens", "$count"]},
                "output_token_average": {"$divide": ["$total_output_tokens", "$count"]},
                "total_token_average": {"$divide": ["$total_tokens", "$count"]},
                "total_requests": "$count"
            }
        }
    ]

    results = list(collection.aggregate(pipeline))

    question_data_dict = defaultdict(lambda: {
        "model_4o_mini": {"input_token_average": 0, "output_token_average": 0, "total_token_average": 0},
        "gemini_1_5_flash": {"input_token_average": 0, "output_token_average": 0, "total_token_average": 0},
        "total_requests": 0
    })

    overall_averages = {
        "model_4o_mini": {"input_token_average": 0, "output_token_average": 0, "total_token_average": 0},
        "gemini_1_5_flash": {"input_token_average": 0, "output_token_average": 0, "total_token_average": 0}
    }
    overall_counts = {
        "model_4o_mini": 0,
        "gemini_1_5_flash": 0
    }

    for result in results:
        model_key = "model_4o_mini" if "4o-mini" in result["model_name"] else "gemini_1_5_flash"
        question_type = result.get("question_type", "unknown")
        question_data_dict[question_type][model_key] = {
            "input_token_average": result["input_token_average"],
            "output_token_average": result["output_token_average"],
            "total_token_average": result["total_token_average"]
        }
        question_data_dict[question_type]["total_requests"] = result["total_requests"]

        overall_averages[model_key]["input_token_average"] += result["input_token_average"] * result["total_requests"]
        overall_averages[model_key]["output_token_average"] += result["output_token_average"] * result["total_requests"]
        overall_averages[model_key]["total_token_average"] += result["total_token_average"] * result["total_requests"]
        overall_counts[model_key] += result["total_requests"]

    for model_key in overall_averages:
        if overall_counts[model_key] > 0:
            overall_averages[model_key]["input_token_average"] /= overall_counts[model_key]
            overall_averages[model_key]["output_token_average"] /= overall_counts[model_key]
            overall_averages[model_key]["total_token_average"] /= overall_counts[model_key]

    response = {
        "questions_data": [
            QuestionData(
                question_type=question_type,
                total_requests=data["total_requests"],
                model_4o_mini=TokenAverages(**data["model_4o_mini"]),
                gemini_1_5_flash=TokenAverages(**data["gemini_1_5_flash"])
            )
            for question_type, data in question_data_dict.items()
        ],
        "overall_averages": OverallAverages(
            model_4o_mini=TokenAverages(**overall_averages["model_4o_mini"]),
            gemini_1_5_flash=TokenAverages(**overall_averages["gemini_1_5_flash"])
        )
    }

    return response

@router.get("/credits/{user_id}", response_description="Get credits used by user in a given time period", response_model=List[Dict[str, Any]])
def get_credits_by_user_and_period(
    user_id: str,
    request: Request,
    start_date: str = Query(..., description="Start date in ISO format"),
    end_date: str = Query(..., description="End date in ISO format")
):
    try:
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format.")

    collection = request.app.database["tokenz"]

    pipeline = [
        {
            "$match": {
                "agent_type": "assistant",
                "user_id": user_id,
                "usage_details.type": {"$ne": None},
                "update_time": {"$gte": start_dt, "$lte": end_dt}
            }
        },
        {"$sort": {"update_time": 1}},
        {
            "$group": {
                "_id": "$thread_id",
                "records": {
                    "$push": {
                        "update_time": "$update_time",
                        "type": "$usage_details.type",
                        "input_tokens": "$usage_details.input_tokens",
                        "output_tokens": "$usage_details.output_tokens",
                        "total_tokens": "$usage_details.total_tokens"
                    }
                }
            }
        },
        {
            "$project": {
                "thread_id": "$_id",
                "credits": {
                    "$reduce": {
                        "input": "$records",
                        "initialValue": {"groupings": [], "temp": []},
                        "in": {
                            "$cond": [
                                {"$eq": ["$$this.type", "tool_call"]},
                                {"groupings": "$$value.groupings", "temp": ["$$this"]},
                                {
                                    "groupings": {
                                        "$concatArrays": [
                                            "$$value.groupings",
                                            [
                                                {"$concatArrays": ["$$value.temp", ["$$this"]]}
                                            ]
                                        ]
                                    },
                                    "temp": []
                                }
                            ]
                        }
                    }
                }
            }
        },
        {"$unwind": "$credits.groupings"},
        {
            "$project": {
                "thread_id": 1,
                "input_tokens": {"$sum": "$credits.groupings.input_tokens"},
                "output_tokens": {"$sum": "$credits.groupings.output_tokens"},
                "total_tokens": {"$sum": "$credits.groupings.total_tokens"},
                "records": "$credits.groupings"
            }
        }
    ]

    results = list(collection.aggregate(pipeline))
    for r in results:
        # Convert datetime to isoformat for JSON serialization
        for rec in r.get("records", []):
            if isinstance(rec.get("update_time"), datetime):
                rec["update_time"] = rec["update_time"].isoformat()
    return results

@router.get("/credits", response_description="Get credits for all users with pagination", response_model=List[Dict[str, Any]])
def get_credits_for_all_users(
    request: Request,
    limit: int = Query(None, description="Limit number of users to return. If null, returns all users."),
    skip: int = Query(0, description="Number of users to skip for pagination.")
):
    collection = request.app.database["tokenz"]

    # Get all unique user_ids
    user_ids = collection.distinct("user_id", {"agent_type": "assistant", "usage_details.type": {"$ne": None}})
    user_ids = [uid for uid in user_ids if uid is not None]
    user_ids.sort()

    if limit is not None:
        user_ids = user_ids[skip:skip+limit]
    else:
        user_ids = user_ids[skip:]

    results = []
    for user_id in user_ids:
        pipeline = [
            {
                "$match": {
                    "agent_type": "assistant",
                    "user_id": user_id,
                    "usage_details.type": {"$ne": None}
                }
            },
            {"$sort": {"update_time": 1}},
            {
                "$group": {
                    "_id": "$thread_id",
                    "records": {
                        "$push": {
                            "update_time": "$update_time",
                            "type": "$usage_details.type",
                            "input_tokens": "$usage_details.input_tokens",
                            "output_tokens": "$usage_details.output_tokens",
                            "total_tokens": "$usage_details.total_tokens"
                        }
                    }
                }
            },
            {
                "$project": {
                    "thread_id": "$_id",
                    "credits": {
                        "$reduce": {
                            "input": "$records",
                            "initialValue": {"groupings": [], "temp": []},
                            "in": {
                                "$cond": [
                                    {"$eq": ["$$this.type", "tool_call"]},
                                    {"groupings": "$$value.groupings", "temp": ["$$this"]},
                                    {
                                        "groupings": {
                                            "$concatArrays": [
                                                "$$value.groupings",
                                                [
                                                    {"$concatArrays": ["$$value.temp", ["$$this"]]}
                                                ]
                                            ]
                                        },
                                        "temp": []
                                    }
                                ]
                            }
                        }
                    }
                }
            },
            {"$unwind": "$credits.groupings"},
            {
                "$project": {
                    "thread_id": 1,
                    "input_tokens": {"$sum": "$credits.groupings.input_tokens"},
                    "output_tokens": {"$sum": "$credits.groupings.output_tokens"},
                    "total_tokens": {"$sum": "$credits.groupings.total_tokens"},
                    "records": "$credits.groupings"
                }
            }
        ]
        user_credits = list(collection.aggregate(pipeline))
        for r in user_credits:
            for rec in r.get("records", []):
                if isinstance(rec.get("update_time"), datetime):
                    rec["update_time"] = rec["update_time"].isoformat()
        results.append({
            "user_id": user_id,
            "credits": user_credits
        })

    return results
