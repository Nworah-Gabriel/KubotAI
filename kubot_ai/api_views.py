from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from cloudinary.exceptions import Error
from .models import Task, UserTask, Reward, Referral, Wallet
from .serializers import WalletCreateSerializer, TaskSerializer, UserTaskSerializer, RewardSerializer, ReferralSerializer, WalletSerializer

# ✅ List and Create Tasks
class TaskListCreateView(generics.ListCreateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [AllowAny]
    

# ✅ Complete a Task
class CompleteTaskView(generics.ListCreateAPIView):
    serializer_class = UserTaskSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        """Retrieve completed tasks based on user_id from query parameters."""
        user_id = self.request.query_params.get("user_id")  # Extract user_id from URL params
        if user_id:
            return UserTask.objects.filter(user_id=user_id)
        return UserTask.objects.all()  # Returns all completed tasks if no user_id is provided

    def create(self, request, *args, **kwargs):
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
            user_task = UserTask.objects.create(user_id=user_id, task=task)

            # Add reward
            reward = Reward.objects.create(user_id=user_id, task=task, amount=task.reward_amount)
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

        
        
# View Rewards
class RewardListView(generics.ListAPIView):
    serializer_class = RewardSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Reward.objects.filter(user=self.request.user)
#    {
# "user":"brendan2",
# "eth_address":"0x2d122fEF1613e82C0C90f443b59E54468e16525C",
# "balance":0.0
# }



# ✅ 
class ReferralView(APIView):
    permission_classes = [AllowAny]  # Open API

    def get(self, request, referral_id):
        referrals = Referral.objects.filter(referral_id=referral_id)
        serializer = ReferralSerializer(referrals, many=True)
        
        return Response({
                "success": False,
                "message": "User Referrals fetched",
                "data": serializer.data
            }, status=status.HTTP_400_BAD_REQUEST)
        
    def post(self, request, referral_id):
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

# ✅ View Wallet Balance
class WalletDetailView(APIView):
    serializer_class = WalletSerializer
    permission_classes = [AllowAny]
    

    def get(self, request, username):
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


# ❗Withdraw Tokens (Placeholder for Blockchain Integration)
class WithdrawTokensView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        wallet = Wallet.objects.get(user=request.user)
        amount = float(request.data.get("amount"))

        if amount > wallet.balance:
            return Response({"error": "Insufficient balance."}, status=status.HTTP_400_BAD_REQUEST)

        # Placeholder for Ethereum smart contract call
        # blockchain_transfer(wallet.eth_address, amount)

        wallet.balance -= amount
        wallet.save()

        return Response({"message": f"{amount} tokens withdrawn to your Ethereum wallet."})
