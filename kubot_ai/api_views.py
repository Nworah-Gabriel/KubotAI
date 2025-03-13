from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from cloudinary.exceptions import Error
from .models import Task, UserTask, Reward, Referral, Wallet
from .serializers import WalletCreateSerializer, TaskSerializer, UserTaskSerializer, RewardSerializer, ReferralSerializer, WalletSerializer

# ✅ List and Create Tasks
class TaskListCreateView(generics.ListCreateAPIView):
    """
    API endpoint to list all tasks and create new tasks.

    GET: Retrieve a list of all available tasks.
    POST: Create a new task.

    Permissions:
    - Allows any user.
    """
    
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [AllowAny]
    

# ✅ Complete a Task

# ✅ Complete a Task
class GetCompleteTaskView(APIView):
    """
    API endpoint for getting completed tasks for user.

    GET: Retrieve completed tasks based on `user_id` (query parameter).

    Permissions:
    - Allows any user.
    """
    
   
    permission_classes = [AllowAny]

    def get(self, request, user_id):
        """Retrieve completed tasks based on user_id from query parameters."""
        
        try:
            data = UserTask.objects.filter(user_id=user_id)
            serializer = UserTaskSerializer(data, many=True)
            if user_id:
                return Response({
                        "message": "User completed task fetched successfully",
                        "data": serializer.data,
                    })
        except Error as e:    
            return Response({
                        "message": f"Error: {e}",
                        "data": None
                    })
    
class CompleteTaskView(APIView):
    """
    API endpoint for users to complete tasks.

    POST: Complete a task with `user_id` and `task_id` in the URL.

    Validations:
    - Ensures task exists.
    - Prevents duplicate task completion.
    - Grants reward upon completion.

    Permissions:
    - Allows any user.
    """
    
    serializer_class = UserTaskSerializer
    permission_classes = [AllowAny]
    
   

    def post(self, request, *args, kwargs):
        """Handles task completion based on user_id and task_id in the URL."""
        
        user_id = self.kwargs.get("user_id")
        task_id = self.kwargs.get("task_id")  

        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return Response({"error": "Task not found."}, status=status.HTTP_404_NOT_FOUND)

        # Prevent duplicate completion
        if UserTask.objects.filter(user_id=user_id, task=task).exists():
            return Response({"error": "User has already completed this task."}, status=status.HTTP_400_BAD_REQUEST)

        # Save task completion
        try:
            user_task = UserTask.objects.create(user_id=user_id, task=task, reward_claimed=True)
            user_task.save()
            # Add reward
            reward = Reward.objects.create(user_id=user_id, task=task, amount=task.reward_amount)
            print(reward)
            reward.save()
            return Response({
            "message": f"Task '{task.title}' completed! You earned {task.reward_amount} tokens.",
            "task": UserTaskSerializer(user_task).data,
            "reward": reward.amount
        }, status=status.HTTP_201_CREATED)
        except Error as e:
            return Response({
            "message": f"Error: {e}",
            "task": UserTaskSerializer(user_task).data,
            "reward": None
        })

        
        
# ✅ View Rewards
class RewardListView(APIView):
    """
    API endpoint to retrieve a user's reward list.

    GET: Fetch all rewards associated with the provided `username`.

    Permissions:
    - Allows any user.
    """
    
    permission_classes = [AllowAny]

    def get(self, request, username):
        """Retrieve rewards based on the username."""
        
        reward = Reward.objects.filter(user__user=username)
        serializer = RewardSerializer(reward, many=True)
        return Response(
            {
                "data": serializer.data
            }
        )
#    {
# "user":"brendan2",
# "eth_address":"0x2d122fEF1613e82C0C90f443b59E54468e16525C",
# "balance":0.0
# }



# ✅ 
class ReferralRegisterView(APIView):
    """
    API endpoint to manage user referrals.

    GET: Retrieve all referrals associated with a `referral_id`.
    POST: Register a new referral using `referral_id`.

    Validations:
    - Ensures referred user exists.
    - Prevents duplicate referrals.
    - Grants a reward for successful referrals.

    Permissions:
    - Allows any user.
    """
    
    permission_classes = [AllowAny]

    def get(self, request, referral_id):
        """Retrieve all referrals for a given referral_id."""
        
        referrals = Referral.objects.filter(referral_id=referral_id)
        serializer = ReferralSerializer(referrals, many=True)
        
        return Response({
                "success": False,
                "message": "User Referrals fetched",
                "data": serializer.data
            }, status=status.HTTP_400_BAD_REQUEST)
        
    def post(self, request, referral_id):
        """Register a referral and grant a reward."""

        referred_user_id = referral_id  # Taken from the URL parameter
        serializer = WalletCreateSerializer(data=request.data)

        # Validate serializer first
        if not serializer.is_valid():
            return Response({
                "success": False,
                "message": "Invalid data provided.",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Check if the referred user exists
            referred_user = Wallet.objects.get(referral_id=referred_user_id)

            # Check if a referral already exists
            if Referral.objects.filter(referred_user=referred_user).exists():
                return Response({
                    "success": False,
                    "message": "This user is already referred."
                }, status=status.HTTP_400_BAD_REQUEST)

        except Wallet.DoesNotExist:
            return Response({
                "success": False,
                "message": "Referred user not found."
            }, status=status.HTTP_404_NOT_FOUND)

        # Create the referral
        try:
            # Save serializer data
            new_wallet=serializer.save()
            new_referral = Referral.objects.create(referrer=referred_user, referred_user=new_wallet)
            new_referral.referral_id=referral_id
            new_referral.save()

            # Update balance
            referred_user.balance += 5
            referred_user.save()

            return Response({
                "success": True,
                "message": "Referral successful! You earned 5 tokens."
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                "success": False,
                "message": f"An unexpected error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            

# ✅ Create new user
class RegisterView(APIView):
    """
    API endpoint for user registration and fetching wallet information.

    Methods:
        get(request):
            Retrieve all wallet records from the database.

        post(request):
            Create a new wallet for a user.
    """
    
    permission_classes = [AllowAny]

    def get(self, request):
        """
        Retrieve a list of all wallet records.
        """
        
        new_wallet = Wallet.objects.all()
        serializer = WalletCreateSerializer(new_wallet, many=True)
        
        return Response({
                "success": False,
                "message": "User Referrals fetched",
                "data": serializer.data
            }, status=status.HTTP_400_BAD_REQUEST)
        
    def post(self, request):
        serializer = WalletCreateSerializer(data=request.data)

        # Validate serializer first
        if not serializer.is_valid():
            return Response({
                "success": False,
                "message": "Invalid data provided.",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)


        
        try:
            # Save serializer data
            new_wallet=serializer.save()
            
            return Response({
                "success": True,
                "message": "User created successfully"
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                "success": False,
                "message": f"An unexpected error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
            
# ✅ View Wallet Balance
class WalletDetailView(APIView):
    """
    API endpoint to retrieve wallet balance.

    GET: Fetch wallet balance for a given `username`.

    Permissions:
    - Allows any user.
    """
    
    serializer_class = WalletSerializer
    permission_classes = [AllowAny]
    

    def get(self, request, username):
        """Retrieve the wallet balance for a user."""
        
        try:
            user = Wallet.objects.get(user=username)
            serializer = WalletSerializer(user)
            return Response ({
                "message": "success",
                "data": serializer.data
                })
        except Error as e:
            return Response({
                "message": f"Error: {e}",
                "data": None
            })


# ✅ Withdraw Tokens
class WithdrawTokensView(APIView):
    """
    API endpoint to withdraw tokens from a user's wallet.

    POST: Withdraw a specified `amount` of tokens for a `username`.

    Validations:
    - Ensures sufficient balance before withdrawal.

    Permissions:
    - Allows any user.
    """
    
    permission_classes = [AllowAny]

    def post(self, request, username):
        """Withdraw a specified amount of tokens from a wallet."""
        
        wallet = Wallet.objects.get(user=username)
        amount = float(request.data.get("amount"))

        if amount > wallet.balance:
            return Response({"error": "Insufficient balance."}, status=status.HTTP_400_BAD_REQUEST)

        wallet.balance -= amount
        wallet.save()
        

        return Response({"message": f"{amount} tokens withdrawn to your account."})
    
    
# ✅ fund Tokens
class FundTokensView(APIView):
    """
    API endpoint to add funds (tokens) to a user's balance.

    POST: Fund a specified `amount` of tokens to a `username`.

    Permissions:
    - Allows any user.
    """
    
    permission_classes = [AllowAny]

    def post(self, request, username):
        """Fund a wallet with a specified amount of tokens."""
        
        wallet = Wallet.objects.get(user=username)
        amount = float(request.data.get("amount"))
            
        try:
            wallet.balance += amount
            wallet.save()
        except Error as e:
            return Response({"error": f"{e}"}, status=status.HTTP_400_BAD_REQUEST)
            
        

        return Response({"message": f"{amount} tokens funded to your account."})
