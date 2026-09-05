from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..dependencies import get_current_user
from ..services.ai_service import NoTransactionsError, generate_narrative

router = APIRouter(tags=["narrative"])


@router.post("/narrative", response_model=schemas.NarrativeResponse)
def create_narrative_report(
    request: schemas.NarrativeRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Generates an AI narrative report summarizing the logged-in user's
    own transactions, in the requested tone.
    """
    transactions = (
        db.query(models.Transaction)
        .filter(models.Transaction.user_id == current_user.id)
        .all()
    )

    try:
        narrative = generate_narrative(transactions, request.tone)
    except NoTransactionsError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No transactions to summarize yet. Add some first.",
        )
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to generate the narrative report. Please try again.",
        )

    return schemas.NarrativeResponse(narrative=narrative)
