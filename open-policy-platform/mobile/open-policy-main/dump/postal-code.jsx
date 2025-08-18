import { View, Text, ScrollView, TouchableOpacity, TextInput } from 'react-native'
import React, { useState } from 'react'
import { SafeAreaView } from 'react-native-safe-area-context'
import { Ionicons } from '@expo/vector-icons'
import Checkbox from 'expo-checkbox';
import { Link, router } from 'expo-router';

const PostalCode = () => {
    const [isChecked, setChecked] = useState(false);


  return (
    <SafeAreaView className="bg-white h-full">
    <ScrollView contentContainerStyle={{ height: '100%' }}>
        <View className="flex-1 px-6 pt-8">
        {/* Back Icon and Progress Bar */}
        <View className="flex-row items-center mb-10">
            <TouchableOpacity
                className="mr-9"
                onPress={()=>router.back()}
                >
            <Ionicons name="chevron-back" size={24} color="black" />
            </TouchableOpacity>
            <View className="h-1 w-[202px] bg-gray-200 ml-9">
                <View className="h-1 bg-black w-1/3" />
            </View>
        </View>

        {/* Header */}
        <Text className="text-blue-300 text-center font-semibold mb-5 mt-8">
            OpenPolicy
        </Text>
        <Text className="text-2xl font-bold text-black text-center mb-10">
            Almost there!
        </Text>

        {/* Form */}
        <View className="space-y-6 mt-10 mb-7">
            {/* Phone Number */}
            <View className="mb-8">
            <Text className="text-gray-400 mb-1">Your Phone Number</Text>
            <TextInput
                value="437-988-999"
                className="border-b border-gray-200 pb-2 text-black text-lg"            />
            </View>

            {/* Postal Code */}
            <View className="mb-8">
            <View className="flex-row justify-start items-center">
                <Text className="text-gray-400 mb-1">Postal Code</Text>
                <Ionicons name="information-circle" size={16} color="gray" className="ml-2" />
            </View>
            <TextInput
                value="M2H2W6"
                className="border-b border-gray-200 pb-2 text-black text-lg"
            />
            </View>
        </View>

        {/* Terms and Conditions */}
        <View className="flex-row w-[325px] items-center mt-8 space-x-2 mb-5">
            <Checkbox 
                color={'#222222'}
                className="mr-3"
                value={isChecked} 
                onValueChange={setChecked} 
                />
            <Text className="text-gray-500">
            By continuing, you agree to OpenPolicy’s{' '}
            <Link className="text-black underline" href="/terms-conditions">Terms of Service</Link> and{' '}
            <Link className="text-black underline" href="/privacy-policy">Privacy Policy</Link>.
            </Text>
        </View>

        {/* Next Button */}
        <TouchableOpacity
            disabled={!isChecked}
            className={`mt-10 rounded-full py-4 ${
            isChecked ? 'bg-black' : 'bg-gray-400'
            }`}
            onPress={()=>router.push('/verification-code')}
        >
            <Text className="text-white text-center font-semibold text-lg">
            Next
            </Text>
        </TouchableOpacity>
        </View>
    </ScrollView>
    </SafeAreaView>

  )
}

export default PostalCode